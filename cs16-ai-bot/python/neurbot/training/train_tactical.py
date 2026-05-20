"""Training script for the Tactical Controller.

Supports:
  - Behavioural cloning (supervised learning from demos)
  - Configurable architecture (MLP or Transformer)
  - Mixed precision training
  - TensorBoard logging
  - Checkpointing with best model selection

Usage:
    python -m neurbot.training.train_tactical --dataset data/datasets/tactical.h5
    python -m neurbot.training.train_tactical --synthetic --n-samples 100000
"""

import argparse
import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split
from torch.utils.tensorboard import SummaryWriter

from neurbot.data.dataset import TacticalDataset, TacticalSequenceDataset, create_synthetic_dataset
from neurbot.models.tactical import TacticalController, TacticalMLP, TacticalTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("train_tactical")


class TacticalLoss(nn.Module):
    """Combined loss for tactical controller outputs.

    Handles mixed continuous/discrete action spaces:
      - MSE for continuous actions (movement, aim)
      - BCE for binary actions (fire, jump, etc.)
      - Cross-entropy for categorical (weapon, buy)
    """

    def __init__(
        self,
        continuous_weight: float = 1.0,
        binary_weight: float = 1.0,
        weapon_weight: float = 0.5,
        buy_weight: float = 0.3,
        aim_weight: float = 2.0,
    ):
        super().__init__()
        self.continuous_weight = continuous_weight
        self.binary_weight = binary_weight
        self.weapon_weight = weapon_weight
        self.buy_weight = buy_weight
        self.aim_weight = aim_weight

    def forward(
        self,
        predictions: dict[str, torch.Tensor],
        targets: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        """Compute combined loss.

        Args:
            predictions: model output dict
            targets: (batch, 12) target action tensor

        Returns:
            dict with individual and total losses
        """
        # Continuous actions: move_forward, move_right, aim_pitch, aim_yaw
        target_continuous = targets[:, 0:4]
        pred_continuous = predictions["continuous"]

        # Weight aim more heavily (indices 2, 3)
        weights = torch.ones(4, device=targets.device)
        weights[2:4] = self.aim_weight
        continuous_loss = (weights * (pred_continuous - target_continuous) ** 2).mean()

        # Binary actions: fire, fire2, jump, crouch, reload, use
        target_binary = targets[:, 4:10]
        pred_binary = predictions["binary_logits"]
        binary_loss = F.binary_cross_entropy_with_logits(pred_binary, target_binary)

        # Weapon slot (categorical, 6 classes)
        target_weapon = (targets[:, 10] * 5).long().clamp(0, 5)
        weapon_loss = F.cross_entropy(predictions["weapon_logits"], target_weapon)

        # Buy command (categorical, 31 classes)
        target_buy = (targets[:, 11] * 30).long().clamp(0, 30)
        buy_loss = F.cross_entropy(predictions["buy_logits"], target_buy)

        total = (
            self.continuous_weight * continuous_loss
            + self.binary_weight * binary_loss
            + self.weapon_weight * weapon_loss
            + self.buy_weight * buy_loss
        )

        return {
            "total": total,
            "continuous": continuous_loss,
            "binary": binary_loss,
            "weapon": weapon_loss,
            "buy": buy_loss,
        }


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: TacticalLoss,
    device: torch.device,
    scaler: Optional[torch.amp.GradScaler] = None,
) -> dict[str, float]:
    """Train for one epoch."""
    model.train()
    total_losses: dict[str, float] = {}
    n_batches = 0

    for states, actions in loader:
        states = states.to(device)
        actions = actions.to(device)

        optimizer.zero_grad()

        if scaler is not None:
            with torch.amp.autocast(device_type=device.type):
                predictions = model(states)
                losses = criterion(predictions, actions)

            scaler.scale(losses["total"]).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            predictions = model(states)
            losses = criterion(predictions, actions)
            losses["total"].backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        for key, val in losses.items():
            total_losses[key] = total_losses.get(key, 0.0) + val.item()
        n_batches += 1

    return {k: v / n_batches for k, v in total_losses.items()}


@torch.no_grad()
def validate(
    model: nn.Module,
    loader: DataLoader,
    criterion: TacticalLoss,
    device: torch.device,
) -> dict[str, float]:
    """Validate model."""
    model.eval()
    total_losses: dict[str, float] = {}
    n_batches = 0

    # Also track action-level metrics
    all_preds = []
    all_targets = []

    for states, actions in loader:
        states = states.to(device)
        actions = actions.to(device)

        predictions = model(states)
        losses = criterion(predictions, actions)

        for key, val in losses.items():
            total_losses[key] = total_losses.get(key, 0.0) + val.item()
        n_batches += 1

        # Collect predictions for metrics
        continuous = predictions["continuous"].cpu()
        binary = torch.sigmoid(predictions["binary_logits"]).cpu()
        all_preds.append(torch.cat([continuous, binary], dim=1))
        all_targets.append(actions[:, :10].cpu())

    avg_losses = {k: v / n_batches for k, v in total_losses.items()}

    # Compute accuracy metrics
    preds = torch.cat(all_preds)
    targets = torch.cat(all_targets)

    # Movement direction accuracy (sign match)
    move_acc = ((preds[:, :2].sign() == targets[:, :2].sign()).float().mean()).item()
    avg_losses["move_direction_acc"] = move_acc

    # Aim MSE (in degrees)
    aim_mse = ((preds[:, 2:4] - targets[:, 2:4]) ** 2).mean().item() * 100  # scale back
    avg_losses["aim_mse_deg"] = aim_mse

    # Fire accuracy
    fire_acc = ((preds[:, 4] > 0.5) == (targets[:, 4] > 0.5)).float().mean().item()
    avg_losses["fire_accuracy"] = fire_acc

    return avg_losses


def train(
    dataset_path: str,
    architecture: str = "mlp",
    output_dir: str = "models",
    epochs: int = 100,
    batch_size: int = 256,
    learning_rate: float = 3e-4,
    weight_decay: float = 1e-4,
    device_str: str = "cpu",
    hidden_dims: Optional[list[int]] = None,
    context_length: int = 16,
) -> None:
    """Main training function."""
    device = torch.device(device_str)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load dataset
    logger.info(f"Loading dataset from {dataset_path}")
    if architecture == "transformer":
        dataset = TacticalSequenceDataset(dataset_path, context_length=context_length)
    else:
        dataset = TacticalDataset(dataset_path, normalize=True, augment=True)

    # Split train/val
    n_val = max(1, int(len(dataset) * 0.1))
    n_train = len(dataset) - n_val
    train_set, val_set = random_split(dataset, [n_train, n_val])
    logger.info(f"Dataset: {n_train} train, {n_val} val samples")

    train_loader = DataLoader(
        train_set, batch_size=batch_size, shuffle=True,
        num_workers=2, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(
        val_set, batch_size=batch_size, shuffle=False,
        num_workers=2, pin_memory=True,
    )

    # Build model
    state_dim = dataset.states.shape[1] if hasattr(dataset, "states") else 157

    if architecture == "mlp":
        if hidden_dims is None:
            hidden_dims = [512, 256, 256, 128]
        model = TacticalMLP(
            input_dim=state_dim, action_dim=12, hidden_dims=hidden_dims
        )
    else:
        model = TacticalTransformer(
            input_dim=state_dim, action_dim=12,
            d_model=128, n_heads=4, n_layers=2,
            context_length=context_length,
        )

    model = model.to(device)
    logger.info(f"Model: {sum(p.numel() for p in model.parameters()):,} parameters")

    # Training setup
    criterion = TacticalLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=weight_decay
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # Mixed precision
    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler() if use_amp else None

    # TensorBoard
    writer = SummaryWriter(output_path / "logs")

    best_val_loss = float("inf")
    best_epoch = 0

    for epoch in range(1, epochs + 1):
        t0 = time.time()

        train_losses = train_epoch(model, train_loader, optimizer, criterion, device, scaler)
        val_losses = validate(model, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - t0

        # Log
        lr = optimizer.param_groups[0]["lr"]
        logger.info(
            f"Epoch {epoch}/{epochs} ({elapsed:.1f}s) lr={lr:.6f} | "
            f"Train loss={train_losses['total']:.4f} | "
            f"Val loss={val_losses['total']:.4f} "
            f"aim_mse={val_losses.get('aim_mse_deg', 0):.4f} "
            f"fire_acc={val_losses.get('fire_accuracy', 0):.3f}"
        )

        # TensorBoard
        for key, val in train_losses.items():
            writer.add_scalar(f"train/{key}", val, epoch)
        for key, val in val_losses.items():
            writer.add_scalar(f"val/{key}", val, epoch)
        writer.add_scalar("lr", lr, epoch)

        # Checkpointing
        if val_losses["total"] < best_val_loss:
            best_val_loss = val_losses["total"]
            best_epoch = epoch
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_loss": best_val_loss,
                    "architecture": architecture,
                },
                output_path / "tactical_bc_best.pt",
            )
            logger.info(f"  -> New best model saved (val_loss={best_val_loss:.4f})")

        # Save periodic checkpoint
        if epoch % 10 == 0:
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                },
                output_path / f"tactical_bc_epoch{epoch}.pt",
            )

    writer.close()
    logger.info(f"Training complete. Best model at epoch {best_epoch} (val_loss={best_val_loss:.4f})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Tactical Controller")
    parser.add_argument("--dataset", type=str, help="Path to dataset (.h5 or directory)")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset")
    parser.add_argument("--n-samples", type=int, default=100000, help="Synthetic dataset size")
    parser.add_argument("--architecture", type=str, default="mlp", choices=["mlp", "transformer"])
    parser.add_argument("--output-dir", type=str, default="models")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--hidden-dims", type=int, nargs="+", default=[512, 256, 256, 128])
    parser.add_argument("--context-length", type=int, default=16)
    args = parser.parse_args()

    if args.synthetic:
        dataset_path = Path(args.output_dir) / "synthetic_tactical.h5"
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        create_synthetic_dataset(str(dataset_path), n_samples=args.n_samples)
        args.dataset = str(dataset_path)
    elif args.dataset is None:
        parser.error("Either --dataset or --synthetic is required")

    train(
        dataset_path=args.dataset,
        architecture=args.architecture,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        device_str=args.device,
        hidden_dims=args.hidden_dims,
        context_length=args.context_length,
    )


if __name__ == "__main__":
    main()
