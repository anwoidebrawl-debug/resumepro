"""Tactical Controller - Neural network for real-time aim and movement decisions.

This model runs every server tick (~15ms) and must have inference time <1ms.
It handles micro-level decisions: aim target, movement direction, firing, etc.

Architectures:
  - MLP: Simple feed-forward network, fastest inference
  - Transformer: Sequence-aware model using recent state history
"""

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class TacticalMLP(nn.Module):
    """Multi-layer perceptron tactical controller.

    Fast inference (<0.5ms on CPU) for real-time decisions.
    Takes current game state and outputs continuous/discrete actions.
    """

    def __init__(
        self,
        input_dim: int = 157,
        action_dim: int = 12,
        hidden_dims: Optional[list[int]] = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [512, 256, 256, 128]

        self.input_dim = input_dim
        self.action_dim = action_dim

        # Build MLP layers
        layers: list[nn.Module] = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.LayerNorm(h_dim),
                nn.GELU(),
                nn.Dropout(dropout),
            ])
            prev_dim = h_dim

        self.backbone = nn.Sequential(*layers)

        # Separate heads for continuous and discrete actions
        # Continuous: move_forward, move_right, aim_delta_pitch, aim_delta_yaw
        self.continuous_head = nn.Sequential(
            nn.Linear(prev_dim, 64),
            nn.GELU(),
            nn.Linear(64, 4),
            nn.Tanh(),  # output in [-1, 1]
        )

        # Binary actions: fire, fire2, jump, crouch, reload, use
        self.binary_head = nn.Sequential(
            nn.Linear(prev_dim, 64),
            nn.GELU(),
            nn.Linear(64, 6),
        )

        # Weapon slot selection (0-5)
        self.weapon_head = nn.Sequential(
            nn.Linear(prev_dim, 32),
            nn.GELU(),
            nn.Linear(32, 6),
        )

        # Buy command (0-30)
        self.buy_head = nn.Sequential(
            nn.Linear(prev_dim, 32),
            nn.GELU(),
            nn.Linear(32, 31),
        )

        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(
        self, state: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        """Forward pass.

        Args:
            state: (batch, input_dim) game state tensor

        Returns:
            dict with keys: continuous, binary_logits, weapon_logits, buy_logits
        """
        features = self.backbone(state)

        return {
            "continuous": self.continuous_head(features),
            "binary_logits": self.binary_head(features),
            "weapon_logits": self.weapon_head(features),
            "buy_logits": self.buy_head(features),
        }

    def predict_action(self, state: torch.Tensor) -> torch.Tensor:
        """Predict a single action tensor for inference.

        Args:
            state: (input_dim,) or (1, input_dim) game state

        Returns:
            (action_dim,) action tensor
        """
        if state.dim() == 1:
            state = state.unsqueeze(0)

        with torch.no_grad():
            output = self.forward(state)

        continuous = output["continuous"][0]  # (4,)
        binary = torch.sigmoid(output["binary_logits"][0])  # (6,)
        weapon = torch.softmax(output["weapon_logits"][0], dim=0)  # (6,)
        buy = torch.softmax(output["buy_logits"][0], dim=0)  # (31,)

        # Assemble action tensor
        action = torch.zeros(self.action_dim)
        action[0:4] = continuous
        action[4:10] = binary
        action[10] = float(torch.argmax(weapon)) / 5.0
        action[11] = float(torch.argmax(buy)) / 30.0

        return action


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for transformer."""

    def __init__(self, d_model: int, max_len: int = 128):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))  # (1, max_len, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class TacticalTransformer(nn.Module):
    """Transformer-based tactical controller using recent state history.

    Takes a sequence of recent game states and predicts the next action.
    Slightly higher latency (~1ms) but captures temporal patterns.
    """

    def __init__(
        self,
        input_dim: int = 157,
        action_dim: int = 12,
        d_model: int = 128,
        n_heads: int = 4,
        n_layers: int = 2,
        context_length: int = 16,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.d_model = d_model
        self.context_length = context_length

        # Project input to model dimension
        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_encoding = PositionalEncoding(d_model, context_length)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)

        # Causal mask (prevent attending to future states)
        mask = nn.Transformer.generate_square_subsequent_mask(context_length)
        self.register_buffer("causal_mask", mask)

        # Output heads (same structure as MLP)
        self.continuous_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.GELU(),
            nn.Linear(64, 4),
            nn.Tanh(),
        )

        self.binary_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.GELU(),
            nn.Linear(64, 6),
        )

        self.weapon_head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.GELU(),
            nn.Linear(32, 6),
        )

        self.buy_head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.GELU(),
            nn.Linear(32, 31),
        )

    def forward(
        self, state_seq: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        """Forward pass.

        Args:
            state_seq: (batch, seq_len, input_dim) sequence of game states

        Returns:
            dict with action predictions for the last timestep
        """
        batch_size, seq_len, _ = state_seq.shape

        # Project and add positional encoding
        x = self.input_proj(state_seq)  # (B, T, d_model)
        x = self.pos_encoding(x)

        # Apply transformer with causal mask
        mask = self.causal_mask[:seq_len, :seq_len]
        x = self.transformer(x, mask=mask)  # (B, T, d_model)

        # Use last timestep's representation
        last = x[:, -1, :]  # (B, d_model)

        return {
            "continuous": self.continuous_head(last),
            "binary_logits": self.binary_head(last),
            "weapon_logits": self.weapon_head(last),
            "buy_logits": self.buy_head(last),
        }

    def predict_action(self, state_seq: torch.Tensor) -> torch.Tensor:
        """Predict action from state sequence."""
        if state_seq.dim() == 2:
            state_seq = state_seq.unsqueeze(0)

        with torch.no_grad():
            output = self.forward(state_seq)

        continuous = output["continuous"][0]
        binary = torch.sigmoid(output["binary_logits"][0])
        weapon = torch.softmax(output["weapon_logits"][0], dim=0)
        buy = torch.softmax(output["buy_logits"][0], dim=0)

        action = torch.zeros(12)
        action[0:4] = continuous
        action[4:10] = binary
        action[10] = float(torch.argmax(weapon)) / 5.0
        action[11] = float(torch.argmax(buy)) / 30.0

        return action


class TacticalController:
    """Unified interface for tactical models."""

    def __init__(
        self,
        architecture: str = "mlp",
        checkpoint_path: Optional[str] = None,
        device: str = "cpu",
        **kwargs: int | float | list[int],
    ):
        self.device = torch.device(device)

        if architecture == "mlp":
            self.model = TacticalMLP(**kwargs)
        elif architecture == "transformer":
            self.model = TacticalTransformer(**kwargs)
        else:
            raise ValueError(f"Unknown architecture: {architecture}")

        self.model.to(self.device)
        self.model.eval()

        if checkpoint_path is not None:
            self.load(checkpoint_path)

        # State history buffer for transformer
        self._state_history: list[torch.Tensor] = []
        self._context_length = kwargs.get("context_length", 16)

    def load(self, path: str) -> None:
        checkpoint = torch.load(path, map_location=self.device, weights_only=True)
        if "model_state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["model_state_dict"])
        else:
            self.model.load_state_dict(checkpoint)

    def save(self, path: str) -> None:
        torch.save({"model_state_dict": self.model.state_dict()}, path)

    def predict(self, state_tensor: torch.Tensor) -> torch.Tensor:
        """Predict action from game state.

        Args:
            state_tensor: (input_dim,) current game state

        Returns:
            (action_dim,) action tensor
        """
        state_tensor = state_tensor.to(self.device)

        if isinstance(self.model, TacticalTransformer):
            self._state_history.append(state_tensor)
            if len(self._state_history) > self._context_length:
                self._state_history = self._state_history[-self._context_length:]
            state_seq = torch.stack(self._state_history)
            return self.model.predict_action(state_seq)
        else:
            return self.model.predict_action(state_tensor)

    def reset(self) -> None:
        """Reset state history (e.g., at round start)."""
        self._state_history.clear()

    @property
    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.model.parameters())
