"""Humanization Layer - Makes bot actions appear naturally human.

Applies realistic imperfections to raw neural network outputs:
  - Reaction time delay (Gaussian distributed)
  - Aim smoothing with Bezier curves (no instant flicks)
  - Spray control with learned recoil + noise
  - Mouse micro-movements when idle
  - Occasional mistakes and hesitations
  - Variable movement precision
"""

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.interpolate import CubicSpline


@dataclass
class HumanizationConfig:
    """Configuration for humanization parameters."""

    # Reaction time (ms)
    reaction_time_mean: float = 200.0
    reaction_time_std: float = 50.0
    reaction_time_min: float = 120.0
    reaction_time_max: float = 400.0

    # Aim smoothing
    aim_smoothing: float = 0.15
    aim_noise_std: float = 0.3
    aim_overshoot_factor: float = 0.1

    # Spray control
    spray_inaccuracy: float = 0.15

    # Mouse micro-movements
    idle_jitter_enabled: bool = True
    idle_jitter_amplitude: float = 0.5
    idle_jitter_frequency: float = 2.0

    # Mistakes
    mistake_probability: float = 0.02

    # Movement
    strafe_noise: float = 0.05

    # Difficulty scaling (0.0=bot, 1.0=pro)
    difficulty: float = 0.7


class AimSmoother:
    """Smooths aim transitions using Bezier curves to simulate human mouse movement.

    Instead of snapping to target, generates a curved path with:
    - Initial acceleration
    - Slight overshoot
    - Correction micro-adjustments
    """

    def __init__(self, config: HumanizationConfig):
        self.config = config
        self._current_pitch = 0.0
        self._current_yaw = 0.0
        self._target_pitch = 0.0
        self._target_yaw = 0.0
        self._aim_path: list[tuple[float, float]] = []
        self._path_index = 0
        self._rng = np.random.default_rng()

    def set_target(self, delta_pitch: float, delta_yaw: float) -> None:
        """Set a new aim target and generate a humanized path to it."""
        total_delta = math.sqrt(delta_pitch**2 + delta_yaw**2)

        if total_delta < 0.1:
            self._aim_path = [(delta_pitch, delta_yaw)]
            self._path_index = 0
            return

        # Number of interpolation steps based on distance
        difficulty = self.config.difficulty
        base_steps = max(2, int(total_delta / (2.0 + 3.0 * difficulty)))
        steps = max(2, base_steps + self._rng.integers(-1, 2))

        # Generate Bezier control points with overshoot
        overshoot = self.config.aim_overshoot_factor * (1.0 - difficulty * 0.5)
        noise_scale = self.config.aim_noise_std * (1.0 - difficulty * 0.7)

        # Control points: start -> overshoot target -> settle on target
        t_vals = np.linspace(0, 1, steps)

        # Add slight overshoot
        overshoot_pitch = delta_pitch * (1.0 + overshoot * self._rng.normal())
        overshoot_yaw = delta_yaw * (1.0 + overshoot * self._rng.normal())

        # Ease-in-out curve (slow start, fast middle, slow end)
        ease = 3 * t_vals**2 - 2 * t_vals**3  # smoothstep

        path_pitch = ease * delta_pitch
        path_yaw = ease * delta_yaw

        # Add overshoot at ~70% of path
        overshoot_idx = int(steps * 0.7)
        if overshoot_idx < steps:
            path_pitch[overshoot_idx:] += (overshoot_pitch - delta_pitch) * (
                1.0 - ease[overshoot_idx:]
            ) * 0.5
            path_yaw[overshoot_idx:] += (overshoot_yaw - delta_yaw) * (
                1.0 - ease[overshoot_idx:]
            ) * 0.5

        # Add noise
        noise_p = self._rng.normal(0, noise_scale, steps)
        noise_y = self._rng.normal(0, noise_scale, steps)
        noise_p[0] = 0  # no noise at start
        noise_p[-1] = 0  # no noise at end (must reach target)
        noise_y[0] = 0
        noise_y[-1] = 0

        path_pitch += noise_p
        path_yaw += noise_y

        # Convert to deltas between steps
        self._aim_path = []
        prev_p, prev_y = 0.0, 0.0
        for i in range(steps):
            dp = path_pitch[i] - prev_p
            dy = path_yaw[i] - prev_y
            self._aim_path.append((dp, dy))
            prev_p = path_pitch[i]
            prev_y = path_yaw[i]

        self._path_index = 0

    def get_next_delta(self) -> tuple[float, float]:
        """Get the next smoothed aim delta."""
        if self._path_index >= len(self._aim_path):
            return (0.0, 0.0)

        delta = self._aim_path[self._path_index]
        self._path_index += 1
        return delta

    @property
    def is_complete(self) -> bool:
        return self._path_index >= len(self._aim_path)


class ReactionTimer:
    """Simulates human reaction time with realistic distribution.

    Uses a shifted log-normal distribution which better matches
    empirical human reaction time data than Gaussian.
    """

    def __init__(self, config: HumanizationConfig):
        self.config = config
        self._rng = np.random.default_rng()
        self._pending_events: deque[tuple[float, dict]] = deque()

    def queue_event(self, event_data: dict) -> None:
        """Queue an event with a reaction time delay."""
        # Sample reaction time from truncated Gaussian
        rt = self._rng.normal(self.config.reaction_time_mean, self.config.reaction_time_std)
        rt = np.clip(rt, self.config.reaction_time_min, self.config.reaction_time_max)

        # Scale by difficulty (pros react faster)
        rt *= 1.0 - 0.3 * self.config.difficulty

        trigger_time = time.monotonic() + rt / 1000.0
        self._pending_events.append((trigger_time, event_data))

    def get_ready_events(self) -> list[dict]:
        """Return events whose reaction time has elapsed."""
        now = time.monotonic()
        ready = []

        while self._pending_events and self._pending_events[0][0] <= now:
            _, event_data = self._pending_events.popleft()
            ready.append(event_data)

        return ready

    def clear(self) -> None:
        self._pending_events.clear()


class SprayController:
    """Simulates human-like spray control with learned patterns + noise.

    CS 1.6 weapons have fixed recoil patterns. Humans learn these patterns
    but execute them imperfectly. This controller:
    1. Knows the weapon's recoil pattern
    2. Applies compensation with configurable accuracy
    3. Adds natural noise that increases with spray duration
    """

    # Simplified recoil patterns for common weapons (pitch, yaw per bullet)
    RECOIL_PATTERNS: dict[int, list[tuple[float, float]]] = {
        15: [  # AK-47 (30 bullets)
            (-1.5, 0.0), (-2.0, 0.0), (-2.5, 0.0), (-2.5, 0.0), (-2.0, 0.0),
            (-1.5, 0.5), (-1.0, 1.0), (-1.0, 1.5), (-0.5, 2.0), (-0.5, 1.5),
            (0.0, 1.0), (0.0, 0.5), (0.5, 0.0), (0.5, -0.5), (0.5, -1.0),
            (0.5, -1.5), (0.0, -2.0), (0.0, -1.5), (-0.5, -1.0), (-0.5, -0.5),
            (-1.0, 0.0), (-1.0, 0.5), (-0.5, 1.0), (0.0, 1.5), (0.0, 1.0),
            (0.5, 0.5), (0.5, 0.0), (0.0, -0.5), (0.0, -1.0), (0.5, -0.5),
        ],
        16: [  # M4A1 (30 bullets)
            (-1.0, 0.0), (-1.5, 0.0), (-2.0, 0.0), (-2.0, 0.0), (-1.5, 0.0),
            (-1.0, 0.3), (-0.5, 0.7), (-0.5, 1.0), (-0.3, 1.3), (-0.3, 1.0),
            (0.0, 0.7), (0.0, 0.3), (0.3, 0.0), (0.3, -0.3), (0.3, -0.7),
            (0.3, -1.0), (0.0, -1.3), (0.0, -1.0), (-0.3, -0.7), (-0.3, -0.3),
            (-0.5, 0.0), (-0.5, 0.3), (-0.3, 0.7), (0.0, 1.0), (0.0, 0.7),
            (0.3, 0.3), (0.3, 0.0), (0.0, -0.3), (0.0, -0.7), (0.3, -0.3),
        ],
    }

    def __init__(self, config: HumanizationConfig):
        self.config = config
        self._rng = np.random.default_rng()
        self._bullet_count = 0
        self._current_weapon = 0

    def start_spray(self, weapon_id: int) -> None:
        self._bullet_count = 0
        self._current_weapon = weapon_id

    def get_compensation(self) -> tuple[float, float]:
        """Get the recoil compensation for the current bullet.

        Returns (pitch_compensation, yaw_compensation) in degrees.
        """
        pattern = self.RECOIL_PATTERNS.get(self._current_weapon)
        if pattern is None or self._bullet_count >= len(pattern):
            return (0.0, 0.0)

        base_p, base_y = pattern[self._bullet_count]
        self._bullet_count += 1

        # Apply accuracy based on difficulty
        accuracy = self.config.difficulty * (1.0 - self.config.spray_inaccuracy)

        # Add noise that increases with spray duration
        spray_factor = 1.0 + self._bullet_count * 0.05
        noise_p = self._rng.normal(0, self.config.spray_inaccuracy * spray_factor)
        noise_y = self._rng.normal(0, self.config.spray_inaccuracy * spray_factor)

        comp_p = -base_p * accuracy + noise_p
        comp_y = -base_y * accuracy + noise_y

        return (comp_p, comp_y)

    def reset(self) -> None:
        self._bullet_count = 0


class IdleJitter:
    """Generates subtle mouse micro-movements when the bot is not actively aiming.

    Real humans never hold their mouse perfectly still - there are always
    small movements from hand tremor, breathing, etc.
    """

    def __init__(self, config: HumanizationConfig):
        self.config = config
        self._rng = np.random.default_rng()
        self._phase = self._rng.uniform(0, 2 * math.pi)
        self._last_time = time.monotonic()

    def get_jitter(self) -> tuple[float, float]:
        if not self.config.idle_jitter_enabled:
            return (0.0, 0.0)

        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        self._phase += dt * self.config.idle_jitter_frequency * 2 * math.pi

        # Perlin-like noise using multiple sine waves
        amp = self.config.idle_jitter_amplitude * (1.0 - self.config.difficulty * 0.5)

        jitter_p = amp * (
            0.5 * math.sin(self._phase * 0.7 + 1.2)
            + 0.3 * math.sin(self._phase * 1.3 + 0.5)
            + 0.2 * self._rng.normal(0, 0.5)
        )

        jitter_y = amp * (
            0.5 * math.sin(self._phase * 0.9 + 2.1)
            + 0.3 * math.sin(self._phase * 1.1 + 1.7)
            + 0.2 * self._rng.normal(0, 0.5)
        )

        return (jitter_p, jitter_y)


class Humanizer:
    """Main humanization layer that applies all imperfections to bot actions.

    Usage:
        humanizer = Humanizer(config)

        # Each tick:
        raw_action = neural_network.predict(state)
        humanized = humanizer.process(raw_action, game_state)
    """

    def __init__(self, config: Optional[HumanizationConfig] = None):
        if config is None:
            config = HumanizationConfig()

        self.config = config
        self.aim_smoother = AimSmoother(config)
        self.reaction_timer = ReactionTimer(config)
        self.spray_controller = SprayController(config)
        self.idle_jitter = IdleJitter(config)
        self._rng = np.random.default_rng()
        self._is_spraying = False
        self._fire_held_ticks = 0

    def process(
        self, action: np.ndarray, is_enemy_visible: bool = False
    ) -> np.ndarray:
        """Apply humanization to a raw action tensor.

        Args:
            action: (12,) raw action from neural network
            is_enemy_visible: whether an enemy is currently visible

        Returns:
            (12,) humanized action tensor
        """
        result = action.copy()

        # Apply aim humanization
        raw_pitch = action[2] * 10.0  # de-normalize
        raw_yaw = action[3] * 10.0

        if is_enemy_visible and abs(raw_pitch) + abs(raw_yaw) > 0.5:
            # Significant aim adjustment - smooth it
            self.aim_smoother.set_target(raw_pitch, raw_yaw)
            dp, dy = self.aim_smoother.get_next_delta()
        elif not is_enemy_visible:
            # Add idle jitter
            dp, dy = self.idle_jitter.get_jitter()
            dp += raw_pitch
            dy += raw_yaw
        else:
            dp, dy = raw_pitch, raw_yaw

        # Add small random noise to aim
        aim_noise = self.config.aim_noise_std * (1.0 - self.config.difficulty * 0.7)
        dp += self._rng.normal(0, aim_noise)
        dy += self._rng.normal(0, aim_noise)

        result[2] = dp / 10.0
        result[3] = dy / 10.0

        # Handle spray control
        if action[4] > 0.5:  # firing
            self._fire_held_ticks += 1
            if self._fire_held_ticks > 1:
                if not self._is_spraying:
                    self._is_spraying = True
                    weapon_id = int(round(action[10] * 5.0))
                    self.spray_controller.start_spray(weapon_id)

                comp_p, comp_y = self.spray_controller.get_compensation()
                result[2] += comp_p / 10.0
                result[3] += comp_y / 10.0
        else:
            self._fire_held_ticks = 0
            if self._is_spraying:
                self._is_spraying = False
                self.spray_controller.reset()

        # Add movement noise
        move_noise = self.config.strafe_noise * (1.0 - self.config.difficulty * 0.5)
        result[0] += self._rng.normal(0, move_noise)
        result[1] += self._rng.normal(0, move_noise)
        result[0] = np.clip(result[0], -1.0, 1.0)
        result[1] = np.clip(result[1], -1.0, 1.0)

        # Occasional mistakes
        if self._rng.random() < self.config.mistake_probability:
            mistake_type = self._rng.integers(0, 4)
            if mistake_type == 0:
                # Wrong weapon switch
                result[10] = self._rng.uniform(0.0, 1.0)
            elif mistake_type == 1:
                # Accidental crouch
                result[7] = 1.0 - result[7]
            elif mistake_type == 2:
                # Brief aim flick (panic)
                result[2] += self._rng.normal(0, 0.3)
                result[3] += self._rng.normal(0, 0.3)
            elif mistake_type == 3:
                # Delayed fire (hesitation) - skip firing this tick
                result[4] = 0.0

        return result

    def reset(self) -> None:
        """Reset humanization state (e.g., at round start)."""
        self.reaction_timer.clear()
        self.spray_controller.reset()
        self._is_spraying = False
        self._fire_held_ticks = 0
