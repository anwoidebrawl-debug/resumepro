"""Shared memory IPC bus for low-latency communication with C++ plugin.

Memory layout:
  [Header: 16 bytes]
    - magic (4B): NEUR
    - version (4B): protocol version
    - state_offset (4B): offset to game state data
    - action_offset (4B): offset to action data
  [State Region: variable]
    - lock byte (1B): 0=free, 1=writing
    - sequence number (4B): monotonically increasing
    - bot_count (4B): number of active bots
    - GameState[MAX_BOTS]: serialized game states
  [Action Region: variable]
    - lock byte (1B): 0=free, 1=writing
    - sequence number (4B)
    - BotAction[MAX_BOTS]: serialized bot actions
"""

import mmap
import os
import struct
import time
from typing import Optional

import numpy as np

from neurbot.ipc.protocol import BotAction, GameState, PlayerInfo, SoundEvent

HEADER_SIZE = 16
STATE_HEADER_SIZE = 9  # lock(1) + seq(4) + bot_count(4)
ACTION_HEADER_SIZE = 5  # lock(1) + seq(4)

# Approximate sizes
STATE_SIZE_PER_BOT = 2048  # generous buffer
ACTION_SIZE_PER_BOT = 64

MAX_BOTS = 10
TOTAL_SHM_SIZE = HEADER_SIZE + STATE_HEADER_SIZE + (STATE_SIZE_PER_BOT * MAX_BOTS) + \
    ACTION_HEADER_SIZE + (ACTION_SIZE_PER_BOT * MAX_BOTS)


class SharedMemoryBus:
    """Manages shared memory communication between Python engine and C++ plugin."""

    def __init__(self, shm_name: str = "/neurbot_state", create: bool = True):
        self.shm_name = shm_name
        self.shm_path = f"/dev/shm{shm_name}"
        self._mm: Optional[mmap.mmap] = None
        self._fd: Optional[int] = None
        self._last_state_seq = 0
        self._last_action_seq = 0

        if create:
            self._create()
        else:
            self._open()

    def _create(self) -> None:
        """Create and initialize shared memory region."""
        # Create file in /dev/shm
        try:
            self._fd = os.open(self.shm_path, os.O_CREAT | os.O_RDWR, 0o666)
        except FileExistsError:
            self._fd = os.open(self.shm_path, os.O_RDWR, 0o666)

        os.ftruncate(self._fd, TOTAL_SHM_SIZE)
        self._mm = mmap.mmap(self._fd, TOTAL_SHM_SIZE)

        # Write header
        state_offset = HEADER_SIZE
        action_offset = HEADER_SIZE + STATE_HEADER_SIZE + (STATE_SIZE_PER_BOT * MAX_BOTS)

        self._mm[0:HEADER_SIZE] = struct.pack(
            "<IIII",
            0x4E455552,  # NEUR magic
            1,  # version
            state_offset,
            action_offset,
        )

        # Initialize state and action regions
        self._mm[state_offset:state_offset + STATE_HEADER_SIZE] = b"\x00" * STATE_HEADER_SIZE
        self._mm[action_offset:action_offset + ACTION_HEADER_SIZE] = b"\x00" * ACTION_HEADER_SIZE

    def _open(self) -> None:
        """Open existing shared memory region."""
        self._fd = os.open(self.shm_path, os.O_RDWR)
        self._mm = mmap.mmap(self._fd, TOTAL_SHM_SIZE)

        # Verify header
        magic, version, _, _ = struct.unpack("<IIII", self._mm[0:HEADER_SIZE])
        if magic != 0x4E455552:
            raise ValueError(f"Invalid magic number: {magic:#x}")
        if version != 1:
            raise ValueError(f"Unsupported protocol version: {version}")

    def _state_offset(self) -> int:
        return struct.unpack("<I", self._mm[8:12])[0]

    def _action_offset(self) -> int:
        return struct.unpack("<I", self._mm[12:16])[0]

    def read_states(self) -> list[GameState]:
        """Read all bot game states from shared memory.

        Returns empty list if no new data since last read.
        """
        if self._mm is None:
            raise RuntimeError("Shared memory not initialized")

        base = self._state_offset()

        # Check lock
        if self._mm[base] != 0:
            return []  # writer is active, skip this tick

        # Read sequence number
        seq = struct.unpack("<I", self._mm[base + 1:base + 5])[0]
        if seq <= self._last_state_seq:
            return []  # no new data

        bot_count = struct.unpack("<I", self._mm[base + 5:base + 9])[0]
        bot_count = min(bot_count, MAX_BOTS)

        states = []
        data_start = base + STATE_HEADER_SIZE

        for i in range(bot_count):
            offset = data_start + (i * STATE_SIZE_PER_BOT)
            state = self._deserialize_state(offset)
            states.append(state)

        self._last_state_seq = seq
        return states

    def write_actions(self, actions: list[BotAction]) -> None:
        """Write bot actions to shared memory."""
        if self._mm is None:
            raise RuntimeError("Shared memory not initialized")

        base = self._action_offset()

        # Set lock
        self._mm[base] = 1

        # Increment sequence
        self._last_action_seq += 1
        self._mm[base + 1:base + 5] = struct.pack("<I", self._last_action_seq)

        # Write actions
        data_start = base + ACTION_HEADER_SIZE
        for i, action in enumerate(actions):
            if i >= MAX_BOTS:
                break
            offset = data_start + (i * ACTION_SIZE_PER_BOT)
            packed = action.pack()
            self._mm[offset:offset + len(packed)] = packed

        # Release lock
        self._mm[base] = 0

    def _deserialize_state(self, offset: int) -> GameState:
        """Deserialize a GameState from shared memory at the given offset."""
        state = GameState()
        mm = self._mm
        pos = offset

        # Header: tick(4) + timestamp(8) + bot_index(4) = 16
        state.tick, state.timestamp, state.bot_index = struct.unpack(
            "<IdI", mm[pos:pos + 16]
        )
        pos += 16

        # Position (3f) + velocity (3f) + view_angles (2f) = 32
        vals = struct.unpack("<3f3f2f", mm[pos:pos + 32])
        state.position = np.array(vals[0:3], dtype=np.float32)
        state.velocity = np.array(vals[3:6], dtype=np.float32)
        state.view_angles = np.array(vals[6:8], dtype=np.float32)
        pos += 32

        # health(f) + armor(f) + money(I) + weapon(I) + ammo_clip(I) + ammo_reserve(I) = 24
        vals = struct.unpack("<ffIIII", mm[pos:pos + 24])
        state.health = vals[0]
        state.armor = vals[1]
        state.money = vals[2]
        state.current_weapon = vals[3]
        state.ammo_clip = vals[4]
        state.ammo_reserve = vals[5]
        pos += 24

        # Booleans: reloading, scoped, crouching, on_ground, alive, team = 6 bytes + padding
        vals = struct.unpack("<5?BI", mm[pos:pos + 10])
        state.is_reloading = vals[0]
        state.is_scoped = vals[1]
        state.is_crouching = vals[2]
        state.is_on_ground = vals[3]
        state.is_alive = vals[4]
        state.team = vals[6]
        pos += 10

        # Enemies: count(I) + MAX_ENEMIES * PlayerInfo
        state.num_enemies = struct.unpack("<I", mm[pos:pos + 4])[0]
        pos += 4
        for i in range(5):
            pinfo = PlayerInfo.unpack(mm[pos:pos + PlayerInfo.STRUCT_SIZE])
            state.enemies[i] = pinfo
            pos += PlayerInfo.STRUCT_SIZE

        # Teammates: count(I) + MAX_TEAMMATES * PlayerInfo
        state.num_teammates = struct.unpack("<I", mm[pos:pos + 4])[0]
        pos += 4
        for i in range(4):
            pinfo = PlayerInfo.unpack(mm[pos:pos + PlayerInfo.STRUCT_SIZE])
            state.teammates[i] = pinfo
            pos += PlayerInfo.STRUCT_SIZE

        # Sounds: count(I) + MAX_SOUNDS * SoundEvent
        state.num_sounds = struct.unpack("<I", mm[pos:pos + 4])[0]
        pos += 4
        for i in range(8):
            snd = SoundEvent.unpack(mm[pos:pos + SoundEvent.STRUCT_SIZE])
            state.sounds[i] = snd
            pos += SoundEvent.STRUCT_SIZE

        # Round context
        vals = struct.unpack("<fIi3fII?", mm[pos:pos + 33])
        state.round_time = vals[0]
        state.round_number = vals[1]
        state.bomb_state = vals[2]
        state.bomb_position = np.array(vals[3:6], dtype=np.float32)
        state.score_t = vals[6]
        state.score_ct = vals[7]
        state.freeze_time = vals[8]
        pos += 33

        # Navigation: 5 waypoint IDs + current area
        vals = struct.unpack("<5iI", mm[pos:pos + 24])
        state.nearest_waypoints = list(vals[0:5])
        state.current_area = vals[5]

        return state

    def close(self) -> None:
        """Close shared memory."""
        if self._mm is not None:
            self._mm.close()
            self._mm = None
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def cleanup(self) -> None:
        """Close and remove shared memory file."""
        self.close()
        try:
            os.unlink(self.shm_path)
        except FileNotFoundError:
            pass

    def __enter__(self) -> "SharedMemoryBus":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
