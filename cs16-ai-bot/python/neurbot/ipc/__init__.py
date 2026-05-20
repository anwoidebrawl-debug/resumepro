"""IPC communication layer for NeurBot."""

from neurbot.ipc.shared_memory import SharedMemoryBus
from neurbot.ipc.protocol import GameState, BotAction

__all__ = ["SharedMemoryBus", "GameState", "BotAction"]
