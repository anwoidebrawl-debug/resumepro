"""Tests for neural network models."""

import numpy as np
import pytest
import torch

from neurbot.models.tactical import TacticalController, TacticalMLP, TacticalTransformer
from neurbot.models.strategic import StrategicPlanner, StrategicTransformer


class TestTacticalMLP:
    def test_forward_shape(self):
        model = TacticalMLP(input_dim=157, action_dim=12)
        state = torch.randn(8, 157)  # batch of 8

        output = model(state)

        assert output["continuous"].shape == (8, 4)
        assert output["binary_logits"].shape == (8, 6)
        assert output["weapon_logits"].shape == (8, 6)
        assert output["buy_logits"].shape == (8, 31)

    def test_predict_action(self):
        model = TacticalMLP(input_dim=157, action_dim=12)
        state = torch.randn(157)

        action = model.predict_action(state)

        assert action.shape == (12,)
        # Continuous actions should be in [-1, 1]
        assert torch.all(action[0:4] >= -1.0)
        assert torch.all(action[0:4] <= 1.0)
        # Binary actions should be probabilities in [0, 1]
        assert torch.all(action[4:10] >= 0.0)
        assert torch.all(action[4:10] <= 1.0)

    def test_custom_hidden_dims(self):
        model = TacticalMLP(input_dim=157, hidden_dims=[128, 64])
        state = torch.randn(4, 157)

        output = model(state)
        assert output["continuous"].shape == (4, 4)

    def test_gradient_flow(self):
        model = TacticalMLP(input_dim=157)
        state = torch.randn(4, 157)

        output = model(state)
        loss = (
            output["continuous"].sum()
            + output["binary_logits"].sum()
            + output["weapon_logits"].sum()
            + output["buy_logits"].sum()
        )
        loss.backward()

        # Check gradients exist for backbone params
        for name, param in model.named_parameters():
            if param.requires_grad and "backbone" in name:
                assert param.grad is not None, f"No gradient for {name}"


class TestTacticalTransformer:
    def test_forward_shape(self):
        model = TacticalTransformer(
            input_dim=157, d_model=64, n_heads=2, n_layers=1, context_length=8
        )
        state_seq = torch.randn(4, 8, 157)

        output = model(state_seq)

        assert output["continuous"].shape == (4, 4)
        assert output["binary_logits"].shape == (4, 6)

    def test_predict_action(self):
        model = TacticalTransformer(
            input_dim=157, d_model=64, n_heads=2, n_layers=1, context_length=8
        )
        state_seq = torch.randn(8, 157)

        action = model.predict_action(state_seq)
        assert action.shape == (12,)

    def test_variable_sequence_length(self):
        model = TacticalTransformer(
            input_dim=157, d_model=64, n_heads=2, n_layers=1, context_length=16
        )

        # Shorter sequence should work
        short_seq = torch.randn(2, 4, 157)
        output = model(short_seq)
        assert output["continuous"].shape == (2, 4)


class TestTacticalController:
    def test_mlp_controller(self):
        controller = TacticalController(
            architecture="mlp",
            device="cpu",
            input_dim=157,
            action_dim=12,
            hidden_dims=[128, 64],
        )

        state = torch.randn(157)
        action = controller.predict(state)

        assert action.shape == (12,)

    def test_transformer_controller(self):
        controller = TacticalController(
            architecture="transformer",
            device="cpu",
            input_dim=157,
            action_dim=12,
            d_model=64,
            n_heads=2,
            n_layers=1,
            context_length=8,
        )

        # Feed multiple states
        for _ in range(5):
            state = torch.randn(157)
            action = controller.predict(state)
            assert action.shape == (12,)

    def test_reset(self):
        controller = TacticalController(
            architecture="transformer",
            device="cpu",
            input_dim=157,
            action_dim=12,
            d_model=64,
            n_heads=2,
            n_layers=1,
        )

        controller.predict(torch.randn(157))
        controller.predict(torch.randn(157))
        controller.reset()
        action = controller.predict(torch.randn(157))
        assert action.shape == (12,)

    def test_num_parameters(self):
        controller = TacticalController(
            architecture="mlp",
            device="cpu",
            input_dim=157,
            action_dim=12,
            hidden_dims=[128, 64],
        )
        assert controller.num_parameters > 0

    def test_invalid_architecture(self):
        with pytest.raises(ValueError):
            TacticalController(architecture="invalid")


class TestStrategicTransformer:
    def test_forward_shape(self):
        model = StrategicTransformer(
            d_model=64, n_heads=2, n_layers=2, context_length=8
        )

        # RoundContext input dim = 12 + 25 + 12 = 49
        round_seq = torch.randn(4, 8, 49)
        output = model(round_seq)

        assert output["strategy_logits"].shape == (4, 16)  # NUM_STRATEGIES
        assert output["buy_logits"].shape == (4, 5)  # NUM_DECISIONS
        assert output["role_logits"].shape == (4, 5, 5)  # 5 players * NUM_ROLES
        assert output["aggression"].shape == (4,)

    def test_aggression_bounded(self):
        model = StrategicTransformer(
            d_model=64, n_heads=2, n_layers=1
        )

        round_seq = torch.randn(2, 4, 49)
        output = model(round_seq)

        assert torch.all(output["aggression"] >= 0.0)
        assert torch.all(output["aggression"] <= 1.0)


class TestStrategicPlanner:
    def test_predict(self):
        planner = StrategicPlanner(
            device="cpu",
            d_model=64,
            n_heads=2,
            n_layers=1,
            context_length=8,
        )

        context = torch.randn(49)
        result = planner.predict(context)

        assert "strategy" in result
        assert "buy_decision" in result
        assert "roles" in result
        assert "aggression" in result

        assert 0 <= result["strategy"] < 16
        assert 0 <= result["buy_decision"] < 5
        assert len(result["roles"]) == 5
        assert 0.0 <= result["aggression"] <= 1.0

    def test_reset(self):
        planner = StrategicPlanner(device="cpu", d_model=64, n_heads=2, n_layers=1)

        planner.predict(torch.randn(49))
        planner.predict(torch.randn(49))
        planner.reset()
        result = planner.predict(torch.randn(49))
        assert "strategy" in result


class TestInferenceBenchmark:
    def test_mlp_inference_fast(self):
        """MLP inference should be <1ms."""
        import time

        model = TacticalMLP(input_dim=157, hidden_dims=[512, 256, 256, 128])
        model.eval()

        # Warmup
        for _ in range(50):
            model.predict_action(torch.randn(157))

        # Benchmark
        times = []
        for _ in range(100):
            state = torch.randn(157)
            t0 = time.monotonic()
            model.predict_action(state)
            times.append((time.monotonic() - t0) * 1000)

        avg_ms = np.mean(times)
        p99_ms = np.percentile(times, 99)

        # Should be well under 1ms on modern hardware
        assert avg_ms < 5.0, f"Average inference too slow: {avg_ms:.2f}ms"
        assert p99_ms < 10.0, f"P99 inference too slow: {p99_ms:.2f}ms"
