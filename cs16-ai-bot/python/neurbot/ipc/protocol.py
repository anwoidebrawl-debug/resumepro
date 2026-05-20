"""IPC protocol definitions for communication between C++ plugin and Python engine.

Defines the binary layout of GameState and BotAction structures that are
exchanged via shared memory. Must be kept in sync with the C++ plugin headers.
"""

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

import numpy as np


# ── Constants ──────────────────────────────────────────────────────────────────

MAX_PLAYERS = 32
MAX_ENEMIES = 5
MAX_TEAMMATES = 4
MAX_SOUNDS = 8
MAX_WAYPOINTS = 5
MAX_BOTS = 10

MAGIC_NUMBER = 0x4E455552  # "NEUR"
PROTOCOL_VERSION = 1


class Team(IntEnum):
    UNASSIGNED = 0
    TERRORIST = 1
    CT = 2
    SPECTATOR = 3


class WeaponID(IntEnum):
    NONE = 0
    KNIFE = 1
    USP = 2
    GLOCK = 3
    DEAGLE = 4
    P228 = 5
    ELITE = 6
    FIVESEVEN = 7
    M3 = 8
    XM1014 = 9
    MP5 = 10
    TMP = 11
    P90 = 12
    MAC10 = 13
    UMP45 = 14
    AK47 = 15
    M4A1 = 16
    SG552 = 17
    AUG = 18
    SCOUT = 19
    AWP = 20
    G3SG1 = 21
    SG550 = 22
    GALIL = 23
    FAMAS = 24
    M249 = 25
    SHIELD = 26
    HE_GRENADE = 27
    FLASHBANG = 28
    SMOKE_GRENADE = 29
    C4 = 30


class SoundType(IntEnum):
    NONE = 0
    FOOTSTEP = 1
    GUNFIRE = 2
    GRENADE_BOUNCE = 3
    GRENADE_EXPLODE = 4
    BOMB_PLANT = 5
    BOMB_DEFUSE = 6
    RELOAD = 7
    SCREAM = 8


class BombState(IntEnum):
    NOT_PLANTED = 0
    PLANTED = 1
    DEFUSING = 2
    EXPLODED = 3
    DEFUSED = 4


# ── Data Structures ───────────────────────────────────────────────────────────


@dataclass
class PlayerInfo:
    """Information about a single player (enemy or teammate)."""

    relative_pos: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    health: float = 0.0
    armor: float = 0.0
    weapon: int = WeaponID.NONE
    visible: bool = False
    alive: bool = False
    time_since_seen: float = 999.0
    distance: float = 0.0

    # Binary format: 3f + 3f + f + f + i + ? + ? + f + f = 40 bytes
    STRUCT_FORMAT = "<3f3fffI??ff"
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT)

    def pack(self) -> bytes:
        return struct.pack(
            self.STRUCT_FORMAT,
            *self.relative_pos,
            *self.velocity,
            self.health,
            self.armor,
            self.weapon,
            self.visible,
            self.alive,
            self.time_since_seen,
            self.distance,
        )

    @classmethod
    def unpack(cls, data: bytes) -> "PlayerInfo":
        values = struct.unpack(cls.STRUCT_FORMAT, data[: cls.STRUCT_SIZE])
        return cls(
            relative_pos=np.array(values[0:3], dtype=np.float32),
            velocity=np.array(values[3:6], dtype=np.float32),
            health=values[6],
            armor=values[7],
            weapon=values[8],
            visible=values[9],
            alive=values[10],
            time_since_seen=values[11],
            distance=values[12],
        )


@dataclass
class SoundEvent:
    """A recent sound event."""

    direction: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    sound_type: int = SoundType.NONE
    time_ago: float = 0.0
    volume: float = 0.0

    STRUCT_FORMAT = "<3fIff"
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT)

    def pack(self) -> bytes:
        return struct.pack(
            self.STRUCT_FORMAT,
            *self.direction,
            self.sound_type,
            self.time_ago,
            self.volume,
        )

    @classmethod
    def unpack(cls, data: bytes) -> "SoundEvent":
        values = struct.unpack(cls.STRUCT_FORMAT, data[: cls.STRUCT_SIZE])
        return cls(
            direction=np.array(values[0:3], dtype=np.float32),
            sound_type=values[3],
            time_ago=values[4],
            volume=values[5],
        )


@dataclass
class GameState:
    """Complete game state for a single bot, sent from C++ plugin to Python.

    Total approximate size: ~1.5KB per bot.
    """

    # Header
    tick: int = 0
    timestamp: float = 0.0
    bot_index: int = 0

    # Self state
    position: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    view_angles: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.float32))
    health: float = 100.0
    armor: float = 0.0
    money: int = 800
    current_weapon: int = WeaponID.KNIFE
    ammo_clip: int = 0
    ammo_reserve: int = 0
    is_reloading: bool = False
    is_scoped: bool = False
    is_crouching: bool = False
    is_on_ground: bool = True
    is_alive: bool = True
    team: int = Team.TERRORIST

    # Visible enemies
    num_enemies: int = 0
    enemies: list[PlayerInfo] = field(
        default_factory=lambda: [PlayerInfo() for _ in range(MAX_ENEMIES)]
    )

    # Teammates
    num_teammates: int = 0
    teammates: list[PlayerInfo] = field(
        default_factory=lambda: [PlayerInfo() for _ in range(MAX_TEAMMATES)]
    )

    # Sound events
    num_sounds: int = 0
    sounds: list[SoundEvent] = field(
        default_factory=lambda: [SoundEvent() for _ in range(MAX_SOUNDS)]
    )

    # Round context
    round_time: float = 0.0
    round_number: int = 0
    bomb_state: int = BombState.NOT_PLANTED
    bomb_position: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    score_t: int = 0
    score_ct: int = 0
    freeze_time: bool = False

    # Navigation
    nearest_waypoints: list[int] = field(default_factory=lambda: [-1] * MAX_WAYPOINTS)
    current_area: int = 0

    def to_tensor(self) -> np.ndarray:
        """Convert game state to a flat numpy array for neural network input."""
        features = []

        # Self state (normalized)
        features.extend(self.position / 4096.0)  # maps are typically <4096 units
        features.extend(self.velocity / 250.0)  # max speed ~250 units/s
        features.extend(self.view_angles / 180.0)  # normalize angles
        features.append(self.health / 100.0)
        features.append(self.armor / 100.0)
        features.append(self.money / 16000.0)
        features.append(float(self.current_weapon) / 30.0)
        features.append(float(self.ammo_clip) / 30.0)
        features.append(float(self.ammo_reserve) / 90.0)
        features.append(float(self.is_reloading))
        features.append(float(self.is_scoped))
        features.append(float(self.is_crouching))
        features.append(float(self.is_on_ground))
        features.append(float(self.team == Team.TERRORIST))

        # Enemies (MAX_ENEMIES * features_per_enemy)
        for i in range(MAX_ENEMIES):
            enemy = self.enemies[i] if i < self.num_enemies else PlayerInfo()
            features.extend(enemy.relative_pos / 4096.0)
            features.extend(enemy.velocity / 250.0)
            features.append(enemy.health / 100.0)
            features.append(float(enemy.weapon) / 30.0)
            features.append(float(enemy.visible))
            features.append(float(enemy.alive))
            features.append(min(enemy.time_since_seen, 30.0) / 30.0)
            features.append(min(enemy.distance, 4096.0) / 4096.0)

        # Teammates (MAX_TEAMMATES * features_per_teammate)
        for i in range(MAX_TEAMMATES):
            tm = self.teammates[i] if i < self.num_teammates else PlayerInfo()
            features.extend(tm.relative_pos / 4096.0)
            features.append(tm.health / 100.0)
            features.append(float(tm.weapon) / 30.0)
            features.append(float(tm.alive))

        # Sound events
        for i in range(MAX_SOUNDS):
            snd = self.sounds[i] if i < self.num_sounds else SoundEvent()
            features.extend(snd.direction)
            features.append(float(snd.sound_type) / 9.0)
            features.append(min(snd.time_ago, 5.0) / 5.0)

        # Round context
        features.append(self.round_time / 115.0)  # max round time
        features.append(float(self.round_number) / 30.0)
        features.append(float(self.bomb_state) / 4.0)
        features.extend(self.bomb_position / 4096.0)
        features.append(float(self.score_t) / 16.0)
        features.append(float(self.score_ct) / 16.0)
        features.append(float(self.freeze_time))

        return np.array(features, dtype=np.float32)

    @staticmethod
    def tensor_dim() -> int:
        """Return the dimensionality of the tensor representation."""
        self_features = 3 + 3 + 2 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1  # 18
        enemy_features = MAX_ENEMIES * (3 + 3 + 1 + 1 + 1 + 1 + 1 + 1)  # 5 * 11 = 55
        teammate_features = MAX_TEAMMATES * (3 + 1 + 1 + 1)  # 4 * 5 = 20  (using 3+1+1+1=6, so 24)
        sound_features = MAX_SOUNDS * (3 + 1 + 1)  # 8 * 5 = 40
        round_features = 1 + 1 + 1 + 3 + 1 + 1 + 1  # 9
        return self_features + enemy_features + teammate_features + sound_features + round_features


@dataclass
class BotAction:
    """Action output from the neural engine, sent back to C++ plugin.

    All values are continuous [-1, 1] or boolean.
    """

    move_forward: float = 0.0  # -1.0 (backward) to 1.0 (forward)
    move_right: float = 0.0  # -1.0 (left) to 1.0 (right)
    aim_delta_pitch: float = 0.0  # mouse Y movement (degrees)
    aim_delta_yaw: float = 0.0  # mouse X movement (degrees)
    fire: bool = False
    fire2: bool = False  # secondary fire (scope/silencer)
    jump: bool = False
    crouch: bool = False
    reload: bool = False
    use: bool = False  # plant/defuse/interact
    weapon_slot: int = 0  # 0=no switch, 1-5=weapon slots
    buy_command: int = 0  # 0=no buy, or specific buy command ID

    STRUCT_FORMAT = "<4f6?2I"
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT)

    def pack(self) -> bytes:
        return struct.pack(
            self.STRUCT_FORMAT,
            self.move_forward,
            self.move_right,
            self.aim_delta_pitch,
            self.aim_delta_yaw,
            self.fire,
            self.fire2,
            self.jump,
            self.crouch,
            self.reload,
            self.use,
            self.weapon_slot,
            self.buy_command,
        )

    @classmethod
    def unpack(cls, data: bytes) -> "BotAction":
        values = struct.unpack(cls.STRUCT_FORMAT, data[: cls.STRUCT_SIZE])
        return cls(
            move_forward=values[0],
            move_right=values[1],
            aim_delta_pitch=values[2],
            aim_delta_yaw=values[3],
            fire=values[4],
            fire2=values[5],
            jump=values[6],
            crouch=values[7],
            reload=values[8],
            use=values[9],
            weapon_slot=values[10],
            buy_command=values[11],
        )

    def to_tensor(self) -> np.ndarray:
        """Convert to numpy array for training."""
        return np.array(
            [
                self.move_forward,
                self.move_right,
                self.aim_delta_pitch / 10.0,  # normalize to roughly [-1, 1]
                self.aim_delta_yaw / 10.0,
                float(self.fire),
                float(self.fire2),
                float(self.jump),
                float(self.crouch),
                float(self.reload),
                float(self.use),
                float(self.weapon_slot) / 5.0,
                float(self.buy_command) / 30.0,
            ],
            dtype=np.float32,
        )

    @staticmethod
    def from_tensor(tensor: np.ndarray) -> "BotAction":
        """Create BotAction from neural network output tensor."""
        return BotAction(
            move_forward=float(np.clip(tensor[0], -1.0, 1.0)),
            move_right=float(np.clip(tensor[1], -1.0, 1.0)),
            aim_delta_pitch=float(tensor[2] * 10.0),
            aim_delta_yaw=float(tensor[3] * 10.0),
            fire=bool(tensor[4] > 0.5),
            fire2=bool(tensor[5] > 0.5),
            jump=bool(tensor[6] > 0.5),
            crouch=bool(tensor[7] > 0.5),
            reload=bool(tensor[8] > 0.5),
            use=bool(tensor[9] > 0.5),
            weapon_slot=int(np.clip(round(tensor[10] * 5.0), 0, 5)),
            buy_command=int(np.clip(round(tensor[11] * 30.0), 0, 30)),
        )

    @staticmethod
    def tensor_dim() -> int:
        return 12
