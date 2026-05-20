"""NeurBot Engine - Main entry point for the Python neural decision engine.

Runs as a separate process, communicating with the C++ plugin via shared memory.
Manages the tactical controller, strategic planner, and humanization layer.

Usage:
    python -m neurbot.engine --config config.yaml
"""

import argparse
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import yaml

from neurbot.humanize.humanizer import Humanizer, HumanizationConfig
from neurbot.ipc.protocol import BotAction, GameState
from neurbot.ipc.shared_memory import SharedMemoryBus
from neurbot.models.tactical import TacticalController
from neurbot.models.strategic import StrategicPlanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("neurbot.engine")


class NeurBotEngine:
    """Main engine that orchestrates all AI components."""

    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self._running = False
        self._tick_count = 0
        self._strategic_interval = 64  # ticks between strategic decisions (~1 second)

        # Initialize components
        self._init_ipc()
        self._init_models()
        self._init_humanizer()

        # Performance tracking
        self._inference_times: list[float] = []
        self._max_latency_ms = self.config["ipc"]["max_latency_ms"]

    def _init_ipc(self) -> None:
        shm_name = self.config["ipc"]["shm_name"]
        logger.info(f"Initializing shared memory IPC: {shm_name}")
        self.ipc = SharedMemoryBus(shm_name=shm_name, create=True)

    def _init_models(self) -> None:
        tac_cfg = self.config["models"]["tactical"]
        device = tac_cfg.get("inference_device", "cpu")

        logger.info(f"Loading tactical controller ({tac_cfg['architecture']}) on {device}")
        self.tactical = TacticalController(
            architecture=tac_cfg["architecture"],
            checkpoint_path=tac_cfg.get("checkpoint"),
            device=device,
            input_dim=tac_cfg.get("input_dim", 157),
            action_dim=tac_cfg.get("action_dim", 12),
            hidden_dims=tac_cfg.get("hidden_dims", [512, 256, 256, 128]),
        )
        logger.info(f"Tactical controller: {self.tactical.num_parameters:,} parameters")

        strat_cfg = self.config["models"]["strategic"]
        logger.info("Loading strategic planner")
        self.strategic = StrategicPlanner(
            checkpoint_path=strat_cfg.get("checkpoint"),
            device=strat_cfg.get("inference_device", "cpu"),
            d_model=strat_cfg.get("d_model", 128),
            n_heads=strat_cfg.get("n_heads", 4),
            n_layers=strat_cfg.get("n_layers", 4),
            context_length=strat_cfg.get("context_length", 64),
        )
        logger.info(f"Strategic planner: {self.strategic.num_parameters:,} parameters")

    def _init_humanizer(self) -> None:
        h_cfg = self.config.get("humanization", {})
        if not h_cfg.get("enabled", True):
            self.humanizer: Optional[Humanizer] = None
            logger.info("Humanization disabled")
            return

        config = HumanizationConfig(
            reaction_time_mean=h_cfg.get("reaction_time_mean", 200.0),
            reaction_time_std=h_cfg.get("reaction_time_std", 50.0),
            reaction_time_min=h_cfg.get("reaction_time_min", 120.0),
            reaction_time_max=h_cfg.get("reaction_time_max", 400.0),
            aim_smoothing=h_cfg.get("aim_smoothing", 0.15),
            aim_noise_std=h_cfg.get("aim_noise_std", 0.3),
            spray_inaccuracy=h_cfg.get("spray_inaccuracy", 0.15),
            idle_jitter_enabled=h_cfg.get("idle_jitter_enabled", True),
            idle_jitter_amplitude=h_cfg.get("idle_jitter_amplitude", 0.5),
            idle_jitter_frequency=h_cfg.get("idle_jitter_frequency", 2.0),
            mistake_probability=h_cfg.get("mistake_probability", 0.02),
            strafe_noise=h_cfg.get("strafe_noise", 0.05),
        )
        self.humanizer = Humanizer(config)
        logger.info("Humanization layer initialized")

    def run(self) -> None:
        """Main engine loop."""
        self._running = True
        logger.info("NeurBot engine started. Waiting for game state...")

        # Track strategic decisions per bot
        current_strategy: dict[int, dict] = {}

        while self._running:
            loop_start = time.monotonic()

            # Read game states from shared memory
            states = self.ipc.read_states()
            if not states:
                # No new data, sleep briefly
                time.sleep(0.001)
                continue

            actions: list[BotAction] = []

            for state in states:
                t0 = time.monotonic()

                # Convert state to tensor
                state_tensor = torch.from_numpy(state.to_tensor())

                # Strategic decisions (every N ticks)
                if self._tick_count % self._strategic_interval == 0:
                    round_ctx = self._build_round_context(state)
                    strategy = self.strategic.predict(round_ctx)
                    current_strategy[state.bot_index] = strategy

                # Tactical decision (every tick)
                action_tensor = self.tactical.predict(state_tensor)
                action_np = action_tensor.numpy()

                # Apply humanization
                is_enemy_visible = any(
                    state.enemies[i].visible for i in range(state.num_enemies)
                )
                if self.humanizer is not None:
                    action_np = self.humanizer.process(action_np, is_enemy_visible)

                # Modulate tactical action based on strategy
                bot_strategy = current_strategy.get(state.bot_index, {})
                action_np = self._apply_strategy(action_np, bot_strategy, state)

                # Convert to BotAction
                action = BotAction.from_tensor(action_np)
                actions.append(action)

                # Track inference time
                inference_ms = (time.monotonic() - t0) * 1000
                self._inference_times.append(inference_ms)

            # Write actions to shared memory
            self.ipc.write_actions(actions)

            self._tick_count += 1

            # Log performance periodically
            if self._tick_count % 640 == 0:  # every ~10 seconds
                self._log_performance()

            # Ensure we don't spin too fast
            elapsed = time.monotonic() - loop_start
            target_interval = 1.0 / self.config["server"]["tickrate"]
            if elapsed < target_interval:
                time.sleep(target_interval - elapsed)

    def _build_round_context(self, state: GameState) -> torch.Tensor:
        """Build round-level context features for strategic planner."""
        features = [
            float(state.score_t) / 16.0,
            float(state.score_ct) / 16.0,
            float(state.round_number) / 30.0,
            float(state.money) / 16000.0,
            0.5,  # team_money_avg (placeholder)
            sum(1 for i in range(state.num_teammates) if state.teammates[i].alive) / 4.0,
            sum(1 for i in range(state.num_enemies) if state.enemies[i].alive) / 5.0,
            float(state.bomb_state) / 4.0,
            state.round_time / 115.0,
            0.0 if state.round_number <= 15 else 1.0,  # half
            0.0,  # loss_streak (placeholder)
            0.0,  # win_streak (placeholder)
            # Player states (5 teammates, simplified)
            state.health / 100.0, state.armor / 100.0,
            float(state.current_weapon) / 30.0, float(state.is_alive), 0.0,
        ]

        # Pad to expected dimension for 5 teammates
        for i in range(4):
            if i < state.num_teammates:
                tm = state.teammates[i]
                features.extend([
                    tm.health / 100.0, tm.armor / 100.0,
                    float(tm.weapon) / 30.0, float(tm.alive), 0.0
                ])
            else:
                features.extend([0.0, 0.0, 0.0, 0.0, 0.0])

        # Recent events (placeholder)
        features.extend([0.0] * 12)

        return torch.tensor(features, dtype=torch.float32)

    def _apply_strategy(
        self, action: np.ndarray, strategy: dict, state: GameState
    ) -> np.ndarray:
        """Modulate tactical action based on strategic decisions."""
        if not strategy:
            return action

        aggression = strategy.get("aggression", 0.5)

        # Adjust movement speed based on aggression
        speed_modifier = 0.5 + aggression * 0.5
        action[0] *= speed_modifier  # forward/back
        action[1] *= speed_modifier  # left/right

        # More aggressive = more likely to fire when enemy visible
        if aggression > 0.7:
            # Lower the fire threshold slightly
            if action[4] > 0.3:
                action[4] = 1.0

        return action

    def _log_performance(self) -> None:
        if not self._inference_times:
            return

        times = self._inference_times[-640:]
        avg_ms = np.mean(times)
        p95_ms = np.percentile(times, 95)
        p99_ms = np.percentile(times, 99)
        max_ms = np.max(times)

        logger.info(
            f"Tick {self._tick_count}: "
            f"inference avg={avg_ms:.2f}ms p95={p95_ms:.2f}ms "
            f"p99={p99_ms:.2f}ms max={max_ms:.2f}ms"
        )

        if p99_ms > self._max_latency_ms:
            logger.warning(
                f"p99 latency ({p99_ms:.2f}ms) exceeds target ({self._max_latency_ms}ms)"
            )

    def stop(self) -> None:
        """Stop the engine."""
        logger.info("Stopping NeurBot engine...")
        self._running = False
        self.ipc.close()

    def handle_signal(self, signum: int, frame: object) -> None:
        self.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="NeurBot Neural Decision Engine")
    parser.add_argument(
        "--config", type=str, default="config.yaml", help="Path to config file"
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Run inference benchmark and exit"
    )
    args = parser.parse_args()

    if args.benchmark:
        run_benchmark(args.config)
        return

    engine = NeurBotEngine(args.config)
    signal.signal(signal.SIGINT, engine.handle_signal)
    signal.signal(signal.SIGTERM, engine.handle_signal)

    try:
        engine.run()
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()


def run_benchmark(config_path: str) -> None:
    """Benchmark inference speed."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    tac_cfg = config["models"]["tactical"]
    controller = TacticalController(
        architecture=tac_cfg["architecture"],
        device=tac_cfg.get("inference_device", "cpu"),
        input_dim=tac_cfg.get("input_dim", 157),
        action_dim=tac_cfg.get("action_dim", 12),
        hidden_dims=tac_cfg.get("hidden_dims", [512, 256, 256, 128]),
    )

    logger.info(f"Model parameters: {controller.num_parameters:,}")

    # Warmup
    dummy = torch.randn(tac_cfg.get("input_dim", 157))
    for _ in range(100):
        controller.predict(dummy)

    # Benchmark
    n_iters = 10000
    times = []
    for _ in range(n_iters):
        state = torch.randn(tac_cfg.get("input_dim", 157))
        t0 = time.monotonic()
        controller.predict(state)
        times.append((time.monotonic() - t0) * 1000)

    times_np = np.array(times)
    logger.info(
        f"Benchmark ({n_iters} iterations):\n"
        f"  Mean:   {np.mean(times_np):.3f} ms\n"
        f"  Median: {np.median(times_np):.3f} ms\n"
        f"  P95:    {np.percentile(times_np, 95):.3f} ms\n"
        f"  P99:    {np.percentile(times_np, 99):.3f} ms\n"
        f"  Max:    {np.max(times_np):.3f} ms"
    )


if __name__ == "__main__":
    main()
