#!/usr/bin/env python3
"""Quick training validation script.

Generates synthetic data, trains a small model for a few epochs,
and runs inference benchmark. Used to validate the full pipeline works.

Usage:
    python scripts/quick_train.py
"""

import sys
import time
from pathlib import Path

# Add python directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

import numpy as np
import torch

from neurbot.data.dataset import TacticalDataset, create_synthetic_dataset
from neurbot.models.tactical import TacticalController, TacticalMLP
from neurbot.humanize.humanizer import Humanizer, HumanizationConfig
from neurbot.ipc.protocol import GameState, BotAction


def main():
    print("=" * 60)
    print("NeurBot Quick Training Validation")
    print("=" * 60)

    output_dir = Path("models")
    output_dir.mkdir(exist_ok=True)
    data_dir = Path("data/datasets")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate synthetic data
    print("\n[1/5] Generating synthetic training data...")
    dataset_path = str(data_dir / "quick_train.h5")
    create_synthetic_dataset(dataset_path, n_samples=10000)

    # Step 2: Create and train model
    print("\n[2/5] Training tactical controller (5 epochs)...")
    dataset = TacticalDataset(dataset_path, normalize=True, augment=True)

    model = TacticalMLP(input_dim=157, action_dim=12, hidden_dims=[256, 128, 64])
    model.train()

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=128, shuffle=True, drop_last=True
    )

    for epoch in range(5):
        total_loss = 0.0
        n_batches = 0
        for states, actions in dataloader:
            optimizer.zero_grad()
            output = model(states)

            # Simplified loss
            cont_loss = torch.nn.functional.mse_loss(output["continuous"], actions[:, 0:4])
            bin_loss = torch.nn.functional.binary_cross_entropy_with_logits(
                output["binary_logits"], actions[:, 4:10]
            )
            loss = cont_loss + bin_loss
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / n_batches
        print(f"  Epoch {epoch + 1}/5: loss={avg_loss:.4f}")

    # Save model
    checkpoint_path = str(output_dir / "quick_train.pt")
    torch.save({"model_state_dict": model.state_dict()}, checkpoint_path)
    print(f"  Model saved to {checkpoint_path}")

    # Step 3: Load model via controller
    print("\n[3/5] Testing model loading and inference...")
    controller = TacticalController(
        architecture="mlp",
        checkpoint_path=checkpoint_path,
        device="cpu",
        input_dim=157,
        action_dim=12,
        hidden_dims=[256, 128, 64],
    )
    print(f"  Model parameters: {controller.num_parameters:,}")

    # Step 4: Inference benchmark
    print("\n[4/5] Running inference benchmark...")
    warmup = 100
    n_iters = 1000

    for _ in range(warmup):
        controller.predict(torch.randn(157))

    times = []
    for _ in range(n_iters):
        state = torch.randn(157)
        t0 = time.monotonic()
        action = controller.predict(state)
        times.append((time.monotonic() - t0) * 1000)

    times_np = np.array(times)
    print(f"  Iterations: {n_iters}")
    print(f"  Mean:   {np.mean(times_np):.3f} ms")
    print(f"  Median: {np.median(times_np):.3f} ms")
    print(f"  P95:    {np.percentile(times_np, 95):.3f} ms")
    print(f"  P99:    {np.percentile(times_np, 99):.3f} ms")
    print(f"  Max:    {np.max(times_np):.3f} ms")

    # Step 5: Test humanization pipeline
    print("\n[5/5] Testing humanization pipeline...")
    config = HumanizationConfig(difficulty=0.7)
    humanizer = Humanizer(config)

    raw_action = controller.predict(torch.randn(157)).numpy()
    humanized = humanizer.process(raw_action, is_enemy_visible=True)

    print(f"  Raw action:       {raw_action[:4]}")
    print(f"  Humanized action: {humanized[:4]}")
    print(f"  Difference:       {np.abs(raw_action[:4] - humanized[:4])}")

    # Convert to BotAction
    bot_action = BotAction.from_tensor(humanized)
    print(f"  BotAction: fwd={bot_action.move_forward:.2f} "
          f"right={bot_action.move_right:.2f} "
          f"fire={bot_action.fire} jump={bot_action.jump}")

    print("\n" + "=" * 60)
    print("All pipeline stages validated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
