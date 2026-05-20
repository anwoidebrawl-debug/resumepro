#!/usr/bin/env python3
"""Batch demo collection and conversion script.

Downloads demo files and converts them to HDF5 training datasets.

Usage:
    # Convert local demos
    python scripts/collect_demos.py --input-dir data/demos/ --output data/datasets/tactical.h5

    # Generate synthetic data for testing
    python scripts/collect_demos.py --synthetic --n-samples 50000 --output data/datasets/synthetic.h5
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

import h5py
import numpy as np

from neurbot.data.demo_parser import demo_to_arrays
from neurbot.data.dataset import create_synthetic_dataset


def convert_demos(input_dir: str, output_path: str, max_frames: int = 0) -> None:
    """Convert all .dem files in a directory to a single HDF5 dataset."""
    demo_dir = Path(input_dir)
    demo_files = sorted(demo_dir.glob("*.dem"))

    if not demo_files:
        print(f"No .dem files found in {input_dir}")
        return

    print(f"Found {len(demo_files)} demo files")

    all_states = []
    all_actions = []

    for i, demo_path in enumerate(demo_files):
        print(f"  [{i+1}/{len(demo_files)}] Parsing {demo_path.name}...")
        try:
            states, actions = demo_to_arrays(str(demo_path), max_frames=max_frames)
            if len(states) > 0:
                all_states.append(states)
                all_actions.append(actions)
                print(f"    -> {len(states)} state-action pairs extracted")
            else:
                print(f"    -> No valid data extracted")
        except Exception as e:
            print(f"    -> Error: {e}")

    if not all_states:
        print("No data extracted from any demos!")
        return

    states = np.concatenate(all_states, axis=0)
    actions = np.concatenate(all_actions, axis=0)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(output_path, "w") as f:
        f.create_dataset("states", data=states, compression="gzip", chunks=True)
        f.create_dataset("actions", data=actions, compression="gzip", chunks=True)
        f.attrs["n_samples"] = len(states)
        f.attrs["state_dim"] = states.shape[1]
        f.attrs["action_dim"] = actions.shape[1]
        f.attrs["n_demos"] = len(demo_files)
        f.attrs["source"] = "demo_parsing"

    print(f"\nDataset saved: {output_path}")
    print(f"  Total samples: {len(states):,}")
    print(f"  State dim: {states.shape[1]}")
    print(f"  Action dim: {actions.shape[1]}")
    print(f"  File size: {Path(output_path).stat().st_size / 1024 / 1024:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="Demo collection and conversion")
    parser.add_argument("--input-dir", type=str, help="Directory with .dem files")
    parser.add_argument("--output", type=str, required=True, help="Output .h5 path")
    parser.add_argument("--max-frames", type=int, default=0, help="Max frames per demo")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic data")
    parser.add_argument("--n-samples", type=int, default=100000, help="Synthetic sample count")
    args = parser.parse_args()

    if args.synthetic:
        create_synthetic_dataset(args.output, n_samples=args.n_samples)
    elif args.input_dir:
        convert_demos(args.input_dir, args.output, args.max_frames)
    else:
        parser.error("Either --input-dir or --synthetic is required")


if __name__ == "__main__":
    main()
