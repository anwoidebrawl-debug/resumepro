"""Reinforcement Learning training for the Tactical Controller.

Uses PPO (Proximal Policy Optimization) to fine-tune a pre-trained
behavioural cloning model through self-play on HLDS servers.

The RL environment communicates with the CS 1.6 server via the same
shared memory IPC used in production inference.

Usage:
    python -m neurbot.training.train_rl --checkpoint models/tactical_bc_best.pt
"""

import argparse
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter

from neurbot.ipc.protocol import BotAction, GameState
from neurbot.ipc.shared_memory import SharedMemoryBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_rl")


@dataclass
class RewardConfig:
    """Reward shaping configuration."""

    kill: float = 1.0
    death: float = -1.0
    bomb_plant: float = 0.5
    bomb_defuse: float = 0.5
    damage_dealt: float = 0.01
    round_win: float = 0.2
    map_control: float = 0.05
    idle_penalty: float = -0.01


class RolloutBuffer:
    """Stores trajectory data for PPO training."""

    def __init__(self, buffer_size: int = 2048, state_dim: int = 157, action_dim: int = 12):
        self.buffer_size = buffer_size
        self.states = np.zeros((buffer_size, state_dim), dtype=np.float32)
        self.actions = np.zeros((buffer_size, action_dim), dtype=np.float32)
        self.rewards = np.zeros(buffer_size, dtype=np.float32)
        self.values = np.zeros(buffer_size, dtype=np.float32)
        self.log_probs = np.zeros(buffer_size, dtype=np.float32)
        self.dones = np.zeros(buffer_size, dtype=np.float32)
        self.advantages = np.zeros(buffer_size, dtype=np.float32)
        self.returns = np.zeros(buffer_size, dtype=np.float32)
        self.ptr = 0

    def add(
        self,
        state: np.ndarray,
        action: np.ndarray,
        reward: float,
        value: float,
        log_prob: float,
        done: bool,
    ) -> None:
        if self.ptr >= self.buffer_size:
            return
        self.states[self.ptr] = state
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.values[self.ptr] = value
        self.log_probs[self.ptr] = log_prob
        self.dones[self.ptr] = float(done)
        self.ptr += 1

    def compute_gae(self, gamma: float = 0.99, gae_lambda: float = 0.95) -> None:
        """Compute Generalized Advantage Estimation."""
        last_gae = 0.0
        for t in reversed(range(self.ptr)):
            if t == self.ptr - 1:
                next_value = 0.0
            else:
                next_value = self.values[t + 1]

            delta = self.rewards[t] + gamma * next_value * (1 - self.dones[t]) - self.values[t]
            last_gae = delta + gamma * gae_lambda * (1 - self.dones[t]) * last_gae
            self.advantages[t] = last_gae
            self.returns[t] = self.advantages[t] + self.values[t]

    def get_batches(self, batch_size: int) -> list[dict[str, torch.Tensor]]:
        """Get randomized mini-batches."""
        indices = np.random.permutation(self.ptr)
        batches = []

        for start in range(0, self.ptr, batch_size):
            end = min(start + batch_size, self.ptr)
            idx = indices[start:end]
            batches.append({
                "states": torch.from_numpy(self.states[idx]),
                "actions": torch.from_numpy(self.actions[idx]),
                "advantages": torch.from_numpy(self.advantages[idx]),
                "returns": torch.from_numpy(self.returns[idx]),
                "old_log_probs": torch.from_numpy(self.log_probs[idx]),
            })

        return batches

    def reset(self) -> None:
        self.ptr = 0


class ActorCritic(nn.Module):
    """Combined actor-critic network for PPO.

    Can be initialized from a pre-trained behavioural cloning model.
    """

    def __init__(self, state_dim: int = 157, action_dim: int = 12, hidden_dim: int = 256):
        super().__init__()

        # Shared backbone
        self.backbone = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
        )

        # Actor head (policy) - outputs action mean
        self.actor_mean = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.GELU(),
            nn.Linear(128, action_dim),
        )
        # Learnable log standard deviation
        self.actor_log_std = nn.Parameter(torch.zeros(action_dim))

        # Critic head (value function)
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.GELU(),
            nn.Linear(128, 1),
        )

    def forward(self, state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.backbone(state)
        action_mean = self.actor_mean(features)
        value = self.critic(features).squeeze(-1)
        return action_mean, value

    def get_action_and_value(
        self, state: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Sample action from policy and return value estimate."""
        action_mean, value = self.forward(state)
        std = self.actor_log_std.exp()

        # Sample from Gaussian
        dist = torch.distributions.Normal(action_mean, std)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=-1)

        return action, log_prob, value

    def evaluate_actions(
        self, state: torch.Tensor, action: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Evaluate given actions under current policy."""
        action_mean, value = self.forward(state)
        std = self.actor_log_std.exp()

        dist = torch.distributions.Normal(action_mean, std)
        log_prob = dist.log_prob(action).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)

        return log_prob, value, entropy

    @classmethod
    def from_pretrained(cls, checkpoint_path: str, **kwargs: int) -> "ActorCritic":
        """Initialize from a pre-trained behavioural cloning model.

        Copies the backbone weights from the BC model.
        """
        model = cls(**kwargs)

        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        bc_state = checkpoint.get("model_state_dict", checkpoint)

        # Try to load matching weights
        model_state = model.state_dict()
        loaded = 0
        for key in model_state:
            if key in bc_state and model_state[key].shape == bc_state[key].shape:
                model_state[key] = bc_state[key]
                loaded += 1

        model.load_state_dict(model_state)
        logger.info(f"Loaded {loaded}/{len(model_state)} weights from pre-trained model")

        return model


def compute_reward(
    prev_state: GameState,
    curr_state: GameState,
    config: RewardConfig,
) -> float:
    """Compute reward signal from state transition."""
    reward = 0.0

    # Kill reward (inferred from score changes)
    # This is simplified - in practice you'd track kills via game events

    # Damage dealt (health difference of visible enemies)
    for i in range(min(curr_state.num_enemies, prev_state.num_enemies)):
        prev_hp = prev_state.enemies[i].health
        curr_hp = curr_state.enemies[i].health
        if curr_hp < prev_hp:
            reward += (prev_hp - curr_hp) * config.damage_dealt

    # Death penalty
    if prev_state.is_alive and not curr_state.is_alive:
        reward += config.death

    # Idle penalty
    speed = np.linalg.norm(curr_state.velocity)
    if speed < 10.0 and curr_state.is_alive:
        reward += config.idle_penalty

    # Bomb events
    if prev_state.bomb_state == 0 and curr_state.bomb_state == 1:
        if curr_state.team == 1:  # Terrorist
            reward += config.bomb_plant

    if prev_state.bomb_state == 1 and curr_state.bomb_state == 4:
        if curr_state.team == 2:  # CT
            reward += config.bomb_defuse

    # Round win
    if curr_state.score_t > prev_state.score_t and curr_state.team == 1:
        reward += config.round_win
    if curr_state.score_ct > prev_state.score_ct and curr_state.team == 2:
        reward += config.round_win

    return reward


def ppo_update(
    model: ActorCritic,
    buffer: RolloutBuffer,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    clip_epsilon: float = 0.2,
    entropy_coef: float = 0.01,
    value_coef: float = 0.5,
    max_grad_norm: float = 0.5,
    n_epochs: int = 10,
    batch_size: int = 64,
) -> dict[str, float]:
    """Perform PPO update."""
    buffer.compute_gae()

    total_policy_loss = 0.0
    total_value_loss = 0.0
    total_entropy = 0.0
    n_updates = 0

    for _ in range(n_epochs):
        for batch in buffer.get_batches(batch_size):
            states = batch["states"].to(device)
            actions = batch["actions"].to(device)
            old_log_probs = batch["old_log_probs"].to(device)
            advantages = batch["advantages"].to(device)
            returns = batch["returns"].to(device)

            # Normalize advantages
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

            # Evaluate current policy
            new_log_probs, values, entropy = model.evaluate_actions(states, actions)

            # PPO clipped objective
            ratio = (new_log_probs - old_log_probs).exp()
            clipped_ratio = ratio.clamp(1 - clip_epsilon, 1 + clip_epsilon)
            policy_loss = -torch.min(ratio * advantages, clipped_ratio * advantages).mean()

            # Value loss
            value_loss = F.mse_loss(values, returns)

            # Total loss
            loss = policy_loss + value_coef * value_loss - entropy_coef * entropy.mean()

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()

            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy += entropy.mean().item()
            n_updates += 1

    return {
        "policy_loss": total_policy_loss / max(n_updates, 1),
        "value_loss": total_value_loss / max(n_updates, 1),
        "entropy": total_entropy / max(n_updates, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="RL Fine-tuning for Tactical Controller")
    parser.add_argument("--checkpoint", type=str, help="Pre-trained BC checkpoint")
    parser.add_argument("--output-dir", type=str, default="models")
    parser.add_argument("--total-steps", type=int, default=1_000_000)
    parser.add_argument("--rollout-steps", type=int, default=2048)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test without server (random states)",
    )
    args = parser.parse_args()

    device = torch.device(args.device)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize model
    if args.checkpoint:
        model = ActorCritic.from_pretrained(args.checkpoint, state_dim=157, action_dim=12)
    else:
        model = ActorCritic(state_dim=157, action_dim=12)

    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    reward_config = RewardConfig()
    writer = SummaryWriter(output_path / "rl_logs")

    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    if args.dry_run:
        logger.info("Running dry-run with random states...")
        buffer = RolloutBuffer(buffer_size=args.rollout_steps)

        for step in range(0, args.total_steps, args.rollout_steps):
            buffer.reset()

            for t in range(args.rollout_steps):
                state = torch.randn(157).to(device)
                action, log_prob, value = model.get_action_and_value(state.unsqueeze(0))

                reward = np.random.randn() * 0.1
                done = np.random.random() < 0.01

                buffer.add(
                    state.cpu().numpy(),
                    action[0].cpu().numpy(),
                    reward,
                    value.item(),
                    log_prob.item(),
                    done,
                )

            losses = ppo_update(model, buffer, optimizer, device)

            iteration = step // args.rollout_steps
            if iteration % 10 == 0:
                logger.info(
                    f"Step {step}/{args.total_steps} | "
                    f"policy_loss={losses['policy_loss']:.4f} "
                    f"value_loss={losses['value_loss']:.4f} "
                    f"entropy={losses['entropy']:.4f}"
                )

            for key, val in losses.items():
                writer.add_scalar(f"rl/{key}", val, step)

        torch.save(
            {"model_state_dict": model.state_dict()},
            output_path / "tactical_rl.pt",
        )
        logger.info("Dry-run complete.")
    else:
        logger.info(
            "Live RL training requires a running CS 1.6 HLDS server with the NeurBot plugin. "
            "Use --dry-run for testing without a server."
        )

    writer.close()


if __name__ == "__main__":
    main()
