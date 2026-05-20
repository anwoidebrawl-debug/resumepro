"""GoldSrc Demo Parser for CS 1.6.

Parses .dem files from CS 1.6 to extract game state and player actions
for building training datasets. Based on the GoldSrc demo format specification.

GoldSrc Demo Format:
  Header: magic(8) + demo_protocol(4) + net_protocol(4) + map_name(260)
          + game_dir(260) + checksum(4) + directory_offset(4)
  Frames: sequence of typed frames with timestamps
  Directory: entry table at end of file

Frame types:
  2 = Demo Start
  3 = Console Command
  4 = Client Data
  5 = Next Section
  6 = Event
  7 = Weapon Animation
  8 = Sound
  9 = Demo Buffer
"""

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Optional

import numpy as np


@dataclass
class DemoHeader:
    magic: str = ""
    demo_protocol: int = 0
    net_protocol: int = 0
    map_name: str = ""
    game_dir: str = ""
    checksum: int = 0
    directory_offset: int = 0


@dataclass
class PlayerState:
    """Extracted player state from a demo frame."""

    timestamp: float = 0.0
    position: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    view_angles: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    buttons: int = 0  # IN_ATTACK, IN_JUMP, etc.
    weapon_id: int = 0
    health: float = 100.0
    armor: float = 0.0
    fov: float = 90.0
    flags: int = 0  # FL_ONGROUND, FL_DUCKING, etc.


@dataclass
class DemoFrame:
    """A single frame from a demo file."""

    frame_type: int = 0
    timestamp: float = 0.0
    frame_index: int = 0
    player_state: Optional[PlayerState] = None
    console_command: str = ""
    raw_data: bytes = b""


@dataclass
class DirectoryEntry:
    """Entry in the demo directory."""

    entry_type: int = 0
    description: str = ""
    flags: int = 0
    cd_track: int = 0
    track_time: float = 0.0
    n_frames: int = 0
    offset: int = 0
    file_length: int = 0


# GoldSrc button flags
IN_ATTACK = 1 << 0
IN_JUMP = 1 << 1
IN_DUCK = 1 << 2
IN_FORWARD = 1 << 3
IN_BACK = 1 << 4
IN_USE = 1 << 5
IN_MOVELEFT = 1 << 9
IN_MOVERIGHT = 1 << 10
IN_ATTACK2 = 1 << 11
IN_RELOAD = 1 << 13

# Player flags
FL_ONGROUND = 1 << 9
FL_DUCKING = 1 << 14


def _read_string(f: BinaryIO, length: int) -> str:
    data = f.read(length)
    return data.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def parse_header(f: BinaryIO) -> DemoHeader:
    """Parse the demo file header."""
    header = DemoHeader()
    header.magic = _read_string(f, 8)

    if header.magic not in ("HLDEMO", "HLDEMO\x00\x00"):
        raise ValueError(f"Not a valid GoldSrc demo file (magic: {header.magic!r})")

    data = f.read(8)
    header.demo_protocol, header.net_protocol = struct.unpack("<II", data)
    header.map_name = _read_string(f, 260)
    header.game_dir = _read_string(f, 260)
    data = f.read(8)
    header.checksum, header.directory_offset = struct.unpack("<II", data)

    return header


def parse_directory(f: BinaryIO, header: DemoHeader) -> list[DirectoryEntry]:
    """Parse the directory at the end of the demo file."""
    f.seek(header.directory_offset)

    n_entries = struct.unpack("<I", f.read(4))[0]
    entries = []

    for _ in range(n_entries):
        entry = DirectoryEntry()
        entry.entry_type = struct.unpack("<I", f.read(4))[0]
        entry.description = _read_string(f, 64)
        data = f.read(24)
        (
            entry.flags,
            entry.cd_track,
            entry.track_time,
            entry.n_frames,
            entry.offset,
            entry.file_length,
        ) = struct.unpack("<IIfIII", data)
        entries.append(entry)

    return entries


def parse_client_data_frame(data: bytes, timestamp: float) -> Optional[PlayerState]:
    """Parse a client data frame to extract player state.

    Client data frame layout (GoldSrc):
      origin(3f) + viewangles(3f) + forward/right/up vectors(9f)
      + various weapon/player state data
    """
    if len(data) < 64:
        return None

    state = PlayerState()
    state.timestamp = timestamp

    try:
        # Origin (position)
        state.position = np.array(
            struct.unpack("<3f", data[0:12]), dtype=np.float32
        )

        # View angles (pitch, yaw, roll)
        state.view_angles = np.array(
            struct.unpack("<3f", data[12:24]), dtype=np.float32
        )

        # Forward velocity can be inferred from frame differences
        # For now, extract what we can from the frame

        # Buttons and weapon info are at variable offsets depending on
        # the exact demo protocol version. Try common offsets.
        if len(data) >= 84:
            state.fov = struct.unpack("<f", data[60:64])[0]

        if len(data) >= 168:
            # Approximate button state location
            state.buttons = struct.unpack("<I", data[164:168])[0]

    except struct.error:
        return None

    return state


def parse_frames(
    f: BinaryIO, entry: DirectoryEntry, max_frames: int = 0
) -> list[DemoFrame]:
    """Parse frames from a directory entry."""
    f.seek(entry.offset)
    frames = []
    end_offset = entry.offset + entry.file_length

    frame_count = 0
    while f.tell() < end_offset:
        if max_frames > 0 and frame_count >= max_frames:
            break

        try:
            frame_type_data = f.read(1)
            if len(frame_type_data) < 1:
                break
            frame_type = struct.unpack("<B", frame_type_data)[0]

            timestamp_data = f.read(4)
            if len(timestamp_data) < 4:
                break
            timestamp = struct.unpack("<f", timestamp_data)[0]

            frame_index_data = f.read(4)
            if len(frame_index_data) < 4:
                break
            frame_index = struct.unpack("<I", frame_index_data)[0]

        except struct.error:
            break

        frame = DemoFrame(
            frame_type=frame_type,
            timestamp=timestamp,
            frame_index=frame_index,
        )

        if frame_type == 2:  # Demo Start
            # Skip demo start data
            f.read(4)  # unknown

        elif frame_type == 3:  # Console Command
            cmd_len_data = f.read(4)
            if len(cmd_len_data) < 4:
                break
            cmd_len = struct.unpack("<I", cmd_len_data)[0]
            cmd_data = f.read(min(cmd_len, 1024))
            frame.console_command = cmd_data.split(b"\x00", 1)[0].decode(
                "ascii", errors="replace"
            )

        elif frame_type == 4:  # Client Data
            # Read client data length
            data_len_bytes = f.read(4)
            if len(data_len_bytes) < 4:
                break
            data_len = struct.unpack("<I", data_len_bytes)[0]
            data = f.read(min(data_len, 65536))
            frame.player_state = parse_client_data_frame(data, timestamp)

        elif frame_type == 5:  # Next Section
            break  # end of this segment

        elif frame_type in (6, 7, 8, 9):  # Event, Weapon Anim, Sound, Buffer
            data_len_bytes = f.read(4)
            if len(data_len_bytes) < 4:
                break
            data_len = struct.unpack("<I", data_len_bytes)[0]
            f.read(min(data_len, 65536))  # skip

        else:
            # Unknown frame type, try to skip
            break

        frames.append(frame)
        frame_count += 1

    return frames


def buttons_to_action(buttons: int, prev_state: PlayerState, curr_state: PlayerState) -> dict:
    """Convert button flags and state changes to action representation."""
    # Infer movement from button flags
    move_forward = 0.0
    if buttons & IN_FORWARD:
        move_forward = 1.0
    elif buttons & IN_BACK:
        move_forward = -1.0

    move_right = 0.0
    if buttons & IN_MOVERIGHT:
        move_right = 1.0
    elif buttons & IN_MOVELEFT:
        move_right = -1.0

    # View angle deltas
    aim_delta = curr_state.view_angles - prev_state.view_angles
    # Handle yaw wraparound
    if aim_delta[1] > 180:
        aim_delta[1] -= 360
    elif aim_delta[1] < -180:
        aim_delta[1] += 360

    return {
        "move_forward": move_forward,
        "move_right": move_right,
        "aim_delta_pitch": float(aim_delta[0]),
        "aim_delta_yaw": float(aim_delta[1]),
        "fire": bool(buttons & IN_ATTACK),
        "fire2": bool(buttons & IN_ATTACK2),
        "jump": bool(buttons & IN_JUMP),
        "crouch": bool(buttons & IN_DUCK),
        "reload": bool(buttons & IN_RELOAD),
        "use": bool(buttons & IN_USE),
    }


def parse_demo(
    demo_path: str, max_frames: int = 0
) -> list[tuple[PlayerState, Optional[dict]]]:
    """Parse a complete demo file and extract (state, action) pairs.

    Args:
        demo_path: path to .dem file
        max_frames: maximum frames to parse (0 = all)

    Returns:
        list of (PlayerState, action_dict) tuples
    """
    path = Path(demo_path)
    if not path.exists():
        raise FileNotFoundError(f"Demo file not found: {demo_path}")

    results: list[tuple[PlayerState, Optional[dict]]] = []

    with open(path, "rb") as f:
        header = parse_header(f)
        directory = parse_directory(f, header)

        for entry in directory:
            if entry.n_frames == 0:
                continue

            frames = parse_frames(f, entry, max_frames)

            # Extract player states and compute actions
            prev_state: Optional[PlayerState] = None
            for frame in frames:
                if frame.player_state is None:
                    continue

                curr_state = frame.player_state
                action = None

                if prev_state is not None:
                    action = buttons_to_action(
                        curr_state.buttons, prev_state, curr_state
                    )

                results.append((curr_state, action))
                prev_state = curr_state

    return results


def demo_to_arrays(
    demo_path: str, max_frames: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Parse a demo and return numpy arrays suitable for training.

    Returns:
        (states, actions) numpy arrays
    """
    pairs = parse_demo(demo_path, max_frames)

    # Filter pairs with valid actions
    valid = [(s, a) for s, a in pairs if a is not None]

    if not valid:
        return np.array([]), np.array([])

    states = []
    actions = []

    for state, action_dict in valid:
        # Convert state to feature vector
        s = np.zeros(157, dtype=np.float32)
        s[0:3] = state.position / 4096.0
        s[3:6] = state.velocity / 250.0
        s[6:8] = state.view_angles[:2] / 180.0
        s[8] = state.health / 100.0
        s[9] = state.armor / 100.0
        # remaining features are zeros (no full game state from single POV demo)

        # Convert action to array
        a = np.array([
            action_dict["move_forward"],
            action_dict["move_right"],
            action_dict["aim_delta_pitch"] / 10.0,
            action_dict["aim_delta_yaw"] / 10.0,
            float(action_dict["fire"]),
            float(action_dict["fire2"]),
            float(action_dict["jump"]),
            float(action_dict["crouch"]),
            float(action_dict["reload"]),
            float(action_dict["use"]),
            0.0,  # weapon slot
            0.0,  # buy command
        ], dtype=np.float32)

        states.append(s)
        actions.append(a)

    return np.array(states), np.array(actions)
