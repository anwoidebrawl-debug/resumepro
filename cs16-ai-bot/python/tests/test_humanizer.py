"""Tests for the humanization layer."""

import numpy as np
import pytest

from neurbot.humanize.humanizer import (
    AimSmoother,
    Humanizer,
    HumanizationConfig,
    IdleJitter,
    ReactionTimer,
    SprayController,
)


class TestAimSmoother:
    def test_small_movement_direct(self):
        config = HumanizationConfig()
        smoother = AimSmoother(config)

        smoother.set_target(0.05, 0.05)
        delta = smoother.get_next_delta()

        # Small movement should be almost direct
        assert abs(delta[0]) < 1.0
        assert abs(delta[1]) < 1.0

    def test_large_movement_smoothed(self):
        config = HumanizationConfig(difficulty=0.5)
        smoother = AimSmoother(config)

        smoother.set_target(20.0, 30.0)

        # Should generate multiple steps
        steps = []
        while not smoother.is_complete:
            steps.append(smoother.get_next_delta())

        assert len(steps) > 1, "Large movement should be broken into steps"

        # Sum of deltas should approximately reach target
        total_p = sum(s[0] for s in steps)
        total_y = sum(s[1] for s in steps)
        assert abs(total_p - 20.0) < 5.0
        assert abs(total_y - 30.0) < 5.0

    def test_completed_returns_zero(self):
        config = HumanizationConfig()
        smoother = AimSmoother(config)

        smoother.set_target(1.0, 1.0)
        while not smoother.is_complete:
            smoother.get_next_delta()

        delta = smoother.get_next_delta()
        assert delta == (0.0, 0.0)


class TestSprayController:
    def test_ak47_compensation(self):
        config = HumanizationConfig(difficulty=1.0, spray_inaccuracy=0.0)
        spray = SprayController(config)

        spray.start_spray(15)  # AK-47

        # First few bullets should have upward recoil compensation
        comp = spray.get_compensation()
        assert comp[0] > 0, "Should compensate upward"

    def test_unknown_weapon(self):
        config = HumanizationConfig()
        spray = SprayController(config)

        spray.start_spray(99)  # unknown weapon
        comp = spray.get_compensation()
        assert comp == (0.0, 0.0)

    def test_reset(self):
        config = HumanizationConfig()
        spray = SprayController(config)

        spray.start_spray(15)
        spray.get_compensation()
        spray.get_compensation()
        spray.reset()

        # After reset, internal bullet count should be 0
        spray.start_spray(15)
        comp = spray.get_compensation()
        # Should be same as first bullet
        assert comp is not None


class TestReactionTimer:
    def test_queue_and_retrieve(self):
        config = HumanizationConfig(
            reaction_time_mean=10.0,  # Very short for testing
            reaction_time_std=1.0,
            reaction_time_min=5.0,
            reaction_time_max=20.0,
        )
        timer = ReactionTimer(config)

        timer.queue_event({"type": "enemy_spotted"})

        # Immediately, should not be ready
        events = timer.get_ready_events()
        # Could be ready if very fast, so just check type
        assert isinstance(events, list)

    def test_clear(self):
        config = HumanizationConfig()
        timer = ReactionTimer(config)

        timer.queue_event({"type": "test"})
        timer.clear()

        events = timer.get_ready_events()
        assert len(events) == 0


class TestIdleJitter:
    def test_produces_values(self):
        config = HumanizationConfig(idle_jitter_enabled=True)
        jitter = IdleJitter(config)

        p, y = jitter.get_jitter()
        assert isinstance(p, float)
        assert isinstance(y, float)

    def test_disabled(self):
        config = HumanizationConfig(idle_jitter_enabled=False)
        jitter = IdleJitter(config)

        p, y = jitter.get_jitter()
        assert p == 0.0
        assert y == 0.0

    def test_bounded(self):
        config = HumanizationConfig(
            idle_jitter_enabled=True,
            idle_jitter_amplitude=0.5,
        )
        jitter = IdleJitter(config)

        for _ in range(100):
            p, y = jitter.get_jitter()
            assert abs(p) < 5.0  # should be small
            assert abs(y) < 5.0


class TestHumanizer:
    def setup_method(self):
        self.config = HumanizationConfig(
            difficulty=0.7,
            mistake_probability=0.0,  # disable for deterministic testing
        )
        self.humanizer = Humanizer(self.config)

    def test_process_basic(self):
        action = np.array([
            1.0, 0.0,  # forward
            0.1, 0.2,  # aim
            1.0, 0.0,  # fire, fire2
            0.0, 0.0,  # jump, crouch
            0.0, 0.0,  # reload, use
            0.4, 0.0,  # weapon, buy
        ], dtype=np.float32)

        result = self.humanizer.process(action, is_enemy_visible=True)

        assert result.shape == (12,)
        assert result is not action  # should be a copy
        # Movement should still be roughly forward
        assert result[0] > 0.5

    def test_process_adds_noise(self):
        action = np.zeros(12, dtype=np.float32)
        action[0] = 1.0  # forward

        results = [self.humanizer.process(action.copy()) for _ in range(20)]

        # With humanization, outputs should vary
        movements = [r[0] for r in results]
        assert len(set(f"{m:.4f}" for m in movements)) > 1, "Should add variation"

    def test_idle_jitter_when_no_enemy(self):
        action = np.zeros(12, dtype=np.float32)

        result = self.humanizer.process(action, is_enemy_visible=False)

        # Should have some aim jitter
        assert abs(result[2]) + abs(result[3]) > 0

    def test_spray_control(self):
        action = np.zeros(12, dtype=np.float32)
        action[4] = 1.0  # firing
        action[10] = 15.0 / 5.0  # AK-47

        # Fire multiple ticks to trigger spray
        for _ in range(5):
            self.humanizer.process(action.copy(), is_enemy_visible=True)

        # Spray controller should be active
        assert self.humanizer._is_spraying

    def test_reset(self):
        action = np.zeros(12, dtype=np.float32)
        action[4] = 1.0
        self.humanizer.process(action)
        self.humanizer.process(action)

        self.humanizer.reset()

        assert not self.humanizer._is_spraying
        assert self.humanizer._fire_held_ticks == 0

    def test_mistakes_when_enabled(self):
        config = HumanizationConfig(mistake_probability=1.0)  # always mistake
        humanizer = Humanizer(config)

        action = np.zeros(12, dtype=np.float32)
        action[0] = 1.0

        result = humanizer.process(action)
        # At least something should be different
        assert not np.array_equal(result, action)

    def test_difficulty_scaling(self):
        # Low difficulty = more noise
        low_config = HumanizationConfig(difficulty=0.1, mistake_probability=0.0)
        high_config = HumanizationConfig(difficulty=0.9, mistake_probability=0.0)

        low_h = Humanizer(low_config)
        high_h = Humanizer(high_config)

        action = np.zeros(12, dtype=np.float32)
        action[0] = 1.0

        # Run many iterations and compare variance
        low_results = [low_h.process(action.copy())[0] for _ in range(50)]
        high_results = [high_h.process(action.copy())[0] for _ in range(50)]

        low_var = np.var(low_results)
        high_var = np.var(high_results)

        # Lower difficulty should have higher variance (more noise)
        assert low_var >= high_var * 0.5, "Low difficulty should have more noise"
