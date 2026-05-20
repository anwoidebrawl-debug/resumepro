"""Tests for IPC protocol structures."""

import numpy as np
import pytest

from neurbot.ipc.protocol import (
    BotAction,
    GameState,
    PlayerInfo,
    SoundEvent,
    Team,
    WeaponID,
    BombState,
    SoundType,
)


class TestPlayerInfo:
    def test_pack_unpack_roundtrip(self):
        info = PlayerInfo(
            relative_pos=np.array([100.0, 200.0, 50.0], dtype=np.float32),
            velocity=np.array([10.0, -5.0, 0.0], dtype=np.float32),
            health=80.0,
            armor=50.0,
            weapon=WeaponID.AK47,
            visible=True,
            alive=True,
            time_since_seen=0.5,
            distance=300.0,
        )

        packed = info.pack()
        unpacked = PlayerInfo.unpack(packed)

        np.testing.assert_array_almost_equal(unpacked.relative_pos, info.relative_pos)
        np.testing.assert_array_almost_equal(unpacked.velocity, info.velocity)
        assert unpacked.health == pytest.approx(80.0)
        assert unpacked.armor == pytest.approx(50.0)
        assert unpacked.weapon == WeaponID.AK47
        assert unpacked.visible is True
        assert unpacked.alive is True
        assert unpacked.time_since_seen == pytest.approx(0.5)
        assert unpacked.distance == pytest.approx(300.0)

    def test_default_values(self):
        info = PlayerInfo()
        assert info.health == 0.0
        assert info.visible is False
        assert info.alive is False

    def test_struct_size(self):
        assert PlayerInfo.STRUCT_SIZE > 0
        packed = PlayerInfo().pack()
        assert len(packed) == PlayerInfo.STRUCT_SIZE


class TestSoundEvent:
    def test_pack_unpack_roundtrip(self):
        snd = SoundEvent(
            direction=np.array([0.5, 0.5, 0.0], dtype=np.float32),
            sound_type=SoundType.GUNFIRE,
            time_ago=1.5,
            volume=0.8,
        )

        packed = snd.pack()
        unpacked = SoundEvent.unpack(packed)

        np.testing.assert_array_almost_equal(unpacked.direction, snd.direction)
        assert unpacked.sound_type == SoundType.GUNFIRE
        assert unpacked.time_ago == pytest.approx(1.5)
        assert unpacked.volume == pytest.approx(0.8)


class TestGameState:
    def test_to_tensor_shape(self):
        state = GameState()
        tensor = state.to_tensor()
        expected_dim = GameState.tensor_dim()

        assert tensor.shape == (expected_dim,)
        assert tensor.dtype == np.float32

    def test_to_tensor_normalization(self):
        state = GameState()
        state.health = 100.0
        state.armor = 50.0
        state.money = 8000

        tensor = state.to_tensor()

        # Health should be normalized to 1.0
        assert tensor[8] == pytest.approx(1.0)
        # Armor should be 0.5
        assert tensor[9] == pytest.approx(0.5)
        # Money should be 0.5
        assert tensor[10] == pytest.approx(0.5)

    def test_to_tensor_with_enemies(self):
        state = GameState()
        state.num_enemies = 1
        state.enemies[0] = PlayerInfo(
            relative_pos=np.array([1000.0, 500.0, 0.0], dtype=np.float32),
            visible=True,
            alive=True,
            health=100.0,
        )

        tensor = state.to_tensor()
        assert tensor is not None
        assert not np.any(np.isnan(tensor))

    def test_tensor_dim_consistency(self):
        """Verify tensor_dim matches actual tensor output."""
        state = GameState()
        state.num_enemies = 3
        state.num_teammates = 2
        state.num_sounds = 4

        tensor = state.to_tensor()
        dim = GameState.tensor_dim()

        assert tensor.shape[0] == dim


class TestBotAction:
    def test_pack_unpack_roundtrip(self):
        action = BotAction(
            move_forward=0.5,
            move_right=-0.3,
            aim_delta_pitch=2.5,
            aim_delta_yaw=-1.0,
            fire=True,
            fire2=False,
            jump=True,
            crouch=False,
            reload=False,
            use=False,
            weapon_slot=3,
            buy_command=0,
        )

        packed = action.pack()
        unpacked = BotAction.unpack(packed)

        assert unpacked.move_forward == pytest.approx(0.5)
        assert unpacked.move_right == pytest.approx(-0.3)
        assert unpacked.aim_delta_pitch == pytest.approx(2.5)
        assert unpacked.fire is True
        assert unpacked.jump is True
        assert unpacked.weapon_slot == 3

    def test_to_tensor(self):
        action = BotAction(
            move_forward=1.0,
            move_right=-1.0,
            aim_delta_pitch=5.0,
            aim_delta_yaw=-3.0,
            fire=True,
        )

        tensor = action.to_tensor()
        assert tensor.shape == (12,)
        assert tensor[0] == pytest.approx(1.0)
        assert tensor[1] == pytest.approx(-1.0)
        assert tensor[2] == pytest.approx(0.5)  # 5.0 / 10.0
        assert tensor[4] == pytest.approx(1.0)  # fire

    def test_from_tensor(self):
        tensor = np.array([
            0.5, -0.3,  # movement
            0.25, -0.1,  # aim (normalized)
            1.0, 0.0,  # fire, fire2
            0.0, 1.0,  # jump, crouch
            0.0, 0.0,  # reload, use
            0.6, 0.0,  # weapon, buy
        ], dtype=np.float32)

        action = BotAction.from_tensor(tensor)
        assert action.move_forward == pytest.approx(0.5)
        assert action.move_right == pytest.approx(-0.3)
        assert action.fire is True
        assert action.crouch is True
        assert action.weapon_slot == 3  # 0.6 * 5 = 3

    def test_tensor_roundtrip(self):
        original = BotAction(
            move_forward=0.7,
            move_right=-0.2,
            aim_delta_pitch=3.0,
            aim_delta_yaw=-2.0,
            fire=True,
            jump=False,
            crouch=True,
        )

        tensor = original.to_tensor()
        restored = BotAction.from_tensor(tensor)

        assert restored.move_forward == pytest.approx(0.7, abs=0.01)
        assert restored.fire is True
        assert restored.crouch is True


class TestEnums:
    def test_team_values(self):
        assert Team.TERRORIST == 1
        assert Team.CT == 2

    def test_weapon_ids(self):
        assert WeaponID.AK47 == 15
        assert WeaponID.M4A1 == 16
        assert WeaponID.AWP == 20

    def test_bomb_state(self):
        assert BombState.NOT_PLANTED == 0
        assert BombState.PLANTED == 1
        assert BombState.DEFUSED == 4
