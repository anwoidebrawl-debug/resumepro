"""Dataset classes for training NeurBot models.

Supports loading from HDF5 files containing (state, action) pairs
extracted from demo files or live gameplay recording.
"""

from pathlib import Path
from typing import Optional

import h5py
import numpy as np
import torch
from torch.utils.data import Dataset


class TacticalDataset(Dataset):
    """Dataset for training the tactical controller.

    Each sample is a (state, action) pair from a single game tick.

    HDF5 format:
        /states: (N, state_dim) float32
        /actions: (N, action_dim) float32
        /metadata/map_name: string
        /metadata/demo_source: string
    """

    def __init__(
        self,
        data_path: str,
        normalize: bool = True,
        augment: bool = True,
    ):
        self.data_path = Path(data_path)
        self.normalize = normalize
        self.augment = augment

        if self.data_path.suffix == ".h5":
            self._load_h5(self.data_path)
        elif self.data_path.is_dir():
            self._load_directory(self.data_path)
        else:
            raise ValueError(f"Unsupported data format: {self.data_path}")

    def _load_h5(self, path: Path) -> None:
        with h5py.File(path, "r") as f:
            self.states = torch.from_numpy(np.array(f["states"], dtype=np.float32))
            self.actions = torch.from_numpy(np.array(f["actions"], dtype=np.float32))

        # Compute normalization stats
        if self.normalize:
            self.state_mean = self.states.mean(dim=0)
            self.state_std = self.states.std(dim=0).clamp(min=1e-6)
        else:
            self.state_mean = torch.zeros(self.states.shape[1])
            self.state_std = torch.ones(self.states.shape[1])

    def _load_directory(self, path: Path) -> None:
        all_states = []
        all_actions = []

        for h5_file in sorted(path.glob("*.h5")):
            with h5py.File(h5_file, "r") as f:
                all_states.append(np.array(f["states"], dtype=np.float32))
                all_actions.append(np.array(f["actions"], dtype=np.float32))

        if not all_states:
            raise ValueError(f"No .h5 files found in {path}")

        self.states = torch.from_numpy(np.concatenate(all_states, axis=0))
        self.actions = torch.from_numpy(np.concatenate(all_actions, axis=0))

        if self.normalize:
            self.state_mean = self.states.mean(dim=0)
            self.state_std = self.states.std(dim=0).clamp(min=1e-6)
        else:
            self.state_mean = torch.zeros(self.states.shape[1])
            self.state_std = torch.ones(self.states.shape[1])

    def __len__(self) -> int:
        return len(self.states)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        state = self.states[idx]
        action = self.actions[idx]

        if self.normalize:
            state = (state - self.state_mean) / self.state_std

        if self.augment and torch.rand(1).item() > 0.5:
            # Mirror augmentation: flip left/right
            state, action = self._mirror(state, action)

        return state, action

    def _mirror(
        self, state: torch.Tensor, action: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Mirror the state and action (flip left/right)."""
        state = state.clone()
        action = action.clone()

        # Flip Y components in position/velocity (indices depend on encoding)
        # Position Y
        state[1] = -state[1]
        # Velocity Y
        state[4] = -state[4]
        # View angle yaw
        state[7] = -state[7]

        # Flip enemy relative positions Y
        for i in range(5):
            base = 18 + i * 11
            state[base + 1] = -state[base + 1]  # relative Y
            state[base + 4] = -state[base + 4]  # velocity Y

        # Flip action: move_right and aim_delta_yaw
        action[1] = -action[1]  # move_right
        action[3] = -action[3]  # aim_delta_yaw

        return state, action


class TacticalSequenceDataset(Dataset):
    """Dataset for transformer-based tactical controller.

    Returns sequences of (state, action) pairs with context.
    """

    def __init__(
        self,
        data_path: str,
        context_length: int = 16,
        normalize: bool = True,
    ):
        self.context_length = context_length
        self.base = TacticalDataset(data_path, normalize=normalize, augment=False)
        self.state_mean = self.base.state_mean
        self.state_std = self.base.state_std

    def __len__(self) -> int:
        return max(0, len(self.base) - self.context_length)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        end_idx = idx + self.context_length

        states = self.base.states[idx:end_idx]
        actions = self.base.actions[end_idx - 1]  # target action for last state

        if self.base.normalize:
            states = (states - self.state_mean) / self.state_std

        return states, actions


class StrategicDataset(Dataset):
    """Dataset for training the strategic planner.

    Each sample is a sequence of round contexts with the target strategy.

    HDF5 format:
        /round_contexts: (N_rounds, context_dim) float32
        /strategies: (N_rounds,) int64
        /buy_decisions: (N_rounds,) int64
        /roles: (N_rounds, 5) int64
        /match_boundaries: (N_matches,) int64  # round indices where matches start
    """

    def __init__(
        self,
        data_path: str,
        context_length: int = 16,
    ):
        self.context_length = context_length

        with h5py.File(data_path, "r") as f:
            self.contexts = torch.from_numpy(np.array(f["round_contexts"], dtype=np.float32))
            self.strategies = torch.from_numpy(np.array(f["strategies"], dtype=np.int64))
            self.buy_decisions = torch.from_numpy(np.array(f["buy_decisions"], dtype=np.int64))

            if "roles" in f:
                self.roles = torch.from_numpy(np.array(f["roles"], dtype=np.int64))
            else:
                self.roles = torch.zeros(len(self.contexts), 5, dtype=torch.int64)

            if "match_boundaries" in f:
                self.match_boundaries = set(
                    np.array(f["match_boundaries"], dtype=np.int64).tolist()
                )
            else:
                self.match_boundaries = set()

        # Build valid indices (don't cross match boundaries)
        self.valid_indices = self._build_valid_indices()

    def _build_valid_indices(self) -> list[int]:
        valid = []
        for i in range(self.context_length, len(self.contexts)):
            # Check if any match boundary falls within the context window
            window = range(i - self.context_length, i)
            if not any(b in self.match_boundaries for b in window):
                valid.append(i)
        return valid

    def __len__(self) -> int:
        return len(self.valid_indices)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        target_idx = self.valid_indices[idx]
        start_idx = target_idx - self.context_length

        return {
            "contexts": self.contexts[start_idx:target_idx],
            "strategy": self.strategies[target_idx],
            "buy_decision": self.buy_decisions[target_idx],
            "roles": self.roles[target_idx],
        }


def create_synthetic_dataset(
    output_path: str,
    n_samples: int = 100000,
    state_dim: int = 157,
    action_dim: int = 12,
) -> None:
    """Create a synthetic dataset for testing the training pipeline.

    Generates random but structurally valid (state, action) pairs.
    """
    rng = np.random.default_rng(42)

    states = rng.standard_normal((n_samples, state_dim)).astype(np.float32)

    # Generate plausible actions
    actions = np.zeros((n_samples, action_dim), dtype=np.float32)
    actions[:, 0] = rng.uniform(-1, 1, n_samples)  # move_forward
    actions[:, 1] = rng.uniform(-1, 1, n_samples)  # move_right
    actions[:, 2] = rng.normal(0, 0.2, n_samples)  # aim_pitch
    actions[:, 3] = rng.normal(0, 0.3, n_samples)  # aim_yaw
    actions[:, 4] = (rng.random(n_samples) > 0.7).astype(np.float32)  # fire
    actions[:, 5] = (rng.random(n_samples) > 0.95).astype(np.float32)  # fire2
    actions[:, 6] = (rng.random(n_samples) > 0.95).astype(np.float32)  # jump
    actions[:, 7] = (rng.random(n_samples) > 0.85).astype(np.float32)  # crouch
    actions[:, 8] = (rng.random(n_samples) > 0.95).astype(np.float32)  # reload
    actions[:, 9] = (rng.random(n_samples) > 0.98).astype(np.float32)  # use
    actions[:, 10] = rng.choice([0, 0.2, 0.4, 0.6, 0.8, 1.0], n_samples)  # weapon
    actions[:, 11] = np.zeros(n_samples)  # buy

    with h5py.File(output_path, "w") as f:
        f.create_dataset("states", data=states, compression="gzip")
        f.create_dataset("actions", data=actions, compression="gzip")
        f.attrs["n_samples"] = n_samples
        f.attrs["state_dim"] = state_dim
        f.attrs["action_dim"] = action_dim
        f.attrs["source"] = "synthetic"

    print(f"Created synthetic dataset: {output_path} ({n_samples} samples)")
