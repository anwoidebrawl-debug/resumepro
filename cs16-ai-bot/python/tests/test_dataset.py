"""Tests for data pipeline."""

import os
import tempfile

import h5py
import numpy as np
import pytest
import torch

from neurbot.data.dataset import (
    TacticalDataset,
    TacticalSequenceDataset,
    create_synthetic_dataset,
)


@pytest.fixture
def synthetic_h5(tmp_path):
    """Create a small synthetic HDF5 dataset for testing."""
    path = str(tmp_path / "test_data.h5")
    create_synthetic_dataset(path, n_samples=1000, state_dim=157, action_dim=12)
    return path


class TestSyntheticDataset:
    def test_create(self, tmp_path):
        path = str(tmp_path / "synth.h5")
        create_synthetic_dataset(path, n_samples=500)

        assert os.path.exists(path)

        with h5py.File(path, "r") as f:
            assert f["states"].shape == (500, 157)
            assert f["actions"].shape == (500, 12)
            assert f.attrs["n_samples"] == 500


class TestTacticalDataset:
    def test_load_h5(self, synthetic_h5):
        dataset = TacticalDataset(synthetic_h5)
        assert len(dataset) == 1000

    def test_getitem(self, synthetic_h5):
        dataset = TacticalDataset(synthetic_h5)
        state, action = dataset[0]

        assert state.shape == (157,)
        assert action.shape == (12,)
        assert state.dtype == torch.float32

    def test_normalization(self, synthetic_h5):
        dataset = TacticalDataset(synthetic_h5, normalize=True)
        state, _ = dataset[0]

        # Normalized state should have reasonable values
        assert torch.all(torch.isfinite(state))

    def test_no_normalization(self, synthetic_h5):
        dataset = TacticalDataset(synthetic_h5, normalize=False)
        state, _ = dataset[0]
        assert torch.all(torch.isfinite(state))

    def test_mirror_augmentation(self, synthetic_h5):
        dataset = TacticalDataset(synthetic_h5, augment=True)

        # Get same item many times - some should be mirrored
        results = [dataset[0] for _ in range(20)]
        states = [r[0] for r in results]

        # With augmentation, should see different values
        # (position Y flipped)
        unique_y = set(float(s[1]) for s in states)
        assert len(unique_y) > 1, "Mirror augmentation should produce variation"

    def test_load_directory(self, tmp_path):
        # Create two H5 files in a directory
        for i in range(2):
            path = str(tmp_path / f"data_{i}.h5")
            create_synthetic_dataset(path, n_samples=100)

        dataset = TacticalDataset(str(tmp_path))
        assert len(dataset) == 200


class TestTacticalSequenceDataset:
    def test_shape(self, synthetic_h5):
        context_length = 16
        dataset = TacticalSequenceDataset(synthetic_h5, context_length=context_length)

        assert len(dataset) == 1000 - context_length

        states, action = dataset[0]
        assert states.shape == (context_length, 157)
        assert action.shape == (12,)

    def test_different_context_lengths(self, synthetic_h5):
        for ctx_len in [4, 8, 32]:
            dataset = TacticalSequenceDataset(synthetic_h5, context_length=ctx_len)
            states, _ = dataset[0]
            assert states.shape == (ctx_len, 157)
