"""Strategic Planner - Transformer model for macro-level game decisions.

Handles high-level strategy that runs every 1-5 seconds:
  - Economy management (buy/save/force/eco)
  - Site selection (A/B attack, default)
  - Role assignment (entry, support, AWPer, lurk)
  - Rotation decisions (based on info)
  - Utility usage planning

Uses round-level context: score, economy, player positions, recent events.
"""

from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from neurbot.models.tactical import PositionalEncoding


class StrategyType:
    """Enumeration of high-level strategies."""

    # T-side strategies
    RUSH_A = 0
    RUSH_B = 1
    SPLIT_A = 2
    SPLIT_B = 3
    DEFAULT = 4
    FAKE_A = 5
    FAKE_B = 6
    MID_CONTROL = 7
    ECO_RUSH = 8
    SAVE = 9

    # CT-side strategies
    STANDARD_HOLD = 10
    STACK_A = 11
    STACK_B = 12
    AGGRO_PUSH_A = 13
    AGGRO_PUSH_B = 14
    RETAKE = 15

    NUM_STRATEGIES = 16


class BuyDecision:
    """Buy decision types."""

    FULL_BUY = 0
    FORCE_BUY = 1
    ECO = 2
    SAVE = 3
    PISTOL_ARMOR = 4

    NUM_DECISIONS = 5


class RoleType:
    """Player roles."""

    ENTRY = 0
    SUPPORT = 1
    AWPER = 2
    LURK = 3
    IGL = 4

    NUM_ROLES = 5


class RoundContext(nn.Module):
    """Encodes round-level context into a fixed-size representation."""

    def __init__(self, d_model: int = 128):
        super().__init__()

        # Round metadata features
        # score_t, score_ct, round_num, money, team_money_avg, team_alive,
        # enemy_alive, bomb_state, round_time, half, loss_streak, win_streak
        self.metadata_dim = 12

        # Player state features (5 teammates)
        # health, armor, weapon_value, alive, has_defuser
        self.player_dim = 5 * 5

        # Recent events (kills, deaths, bomb plants in last 3 rounds)
        self.events_dim = 12

        total_input = self.metadata_dim + self.player_dim + self.events_dim
        self.encoder = nn.Sequential(
            nn.Linear(total_input, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Encode round context.

        Args:
            x: (batch, total_input) round context features

        Returns:
            (batch, d_model) encoded context
        """
        return self.encoder(x)


class StrategicTransformer(nn.Module):
    """Transformer model for strategic decisions.

    Takes a sequence of round contexts (recent round history) and predicts
    the next round's strategy, buy decision, and role assignments.
    """

    def __init__(
        self,
        d_model: int = 128,
        n_heads: int = 4,
        n_layers: int = 4,
        context_length: int = 16,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.context_length = context_length

        self.round_encoder = RoundContext(d_model)
        self.pos_encoding = PositionalEncoding(d_model, context_length)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)

        # Strategy prediction head
        self.strategy_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.GELU(),
            nn.Linear(64, StrategyType.NUM_STRATEGIES),
        )

        # Buy decision head
        self.buy_head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.GELU(),
            nn.Linear(32, BuyDecision.NUM_DECISIONS),
        )

        # Role assignment head (for each of 5 players)
        self.role_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.GELU(),
            nn.Linear(64, 5 * RoleType.NUM_ROLES),
        )

        # Aggression level (0=passive, 1=aggressive)
        self.aggression_head = nn.Sequential(
            nn.Linear(d_model, 16),
            nn.GELU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(
        self, round_seq: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        """Forward pass.

        Args:
            round_seq: (batch, seq_len, context_dim) sequence of round contexts

        Returns:
            dict with strategy, buy, roles, and aggression predictions
        """
        batch_size, seq_len, _ = round_seq.shape

        # Encode each round
        encoded = self.round_encoder(
            round_seq.view(-1, round_seq.size(-1))
        ).view(batch_size, seq_len, -1)

        # Add positional encoding
        encoded = self.pos_encoding(encoded)

        # Transformer
        mask = nn.Transformer.generate_square_subsequent_mask(seq_len).to(encoded.device)
        x = self.transformer(encoded, mask=mask)

        # Use last position
        last = x[:, -1, :]

        # Role logits reshaped to (batch, 5, NUM_ROLES)
        role_logits = self.role_head(last).view(batch_size, 5, RoleType.NUM_ROLES)

        return {
            "strategy_logits": self.strategy_head(last),
            "buy_logits": self.buy_head(last),
            "role_logits": role_logits,
            "aggression": self.aggression_head(last).squeeze(-1),
        }


class StrategicPlanner:
    """High-level strategic planner interface."""

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        device: str = "cpu",
        **kwargs: int | float,
    ):
        self.device = torch.device(device)
        self.model = StrategicTransformer(**kwargs)
        self.model.to(self.device)
        self.model.eval()

        if checkpoint_path is not None:
            self.load(checkpoint_path)

        self._round_history: list[torch.Tensor] = []
        self._context_length = int(kwargs.get("context_length", 16))

    def load(self, path: str) -> None:
        checkpoint = torch.load(path, map_location=self.device, weights_only=True)
        if "model_state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["model_state_dict"])
        else:
            self.model.load_state_dict(checkpoint)

    def save(self, path: str) -> None:
        torch.save({"model_state_dict": self.model.state_dict()}, path)

    def predict(self, round_context: torch.Tensor) -> dict[str, int | float]:
        """Predict strategic decisions for the current round.

        Args:
            round_context: (context_dim,) current round features

        Returns:
            dict with strategy, buy_decision, roles, aggression
        """
        round_context = round_context.to(self.device)
        self._round_history.append(round_context)
        if len(self._round_history) > self._context_length:
            self._round_history = self._round_history[-self._context_length:]

        seq = torch.stack(self._round_history).unsqueeze(0)  # (1, T, D)

        with torch.no_grad():
            output = self.model(seq)

        strategy = int(torch.argmax(output["strategy_logits"][0]))
        buy = int(torch.argmax(output["buy_logits"][0]))
        roles = [int(torch.argmax(output["role_logits"][0, i])) for i in range(5)]
        aggression = float(output["aggression"][0])

        return {
            "strategy": strategy,
            "buy_decision": buy,
            "roles": roles,
            "aggression": aggression,
        }

    def reset(self) -> None:
        """Reset round history (e.g., at half-time or match start)."""
        self._round_history.clear()

    @property
    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.model.parameters())
