/**
 * @file perception.cpp
 * @brief Game state extraction implementation.
 */

#include "perception.h"
#include <cmath>
#include <cstring>

namespace neurbot {

Perception::Perception()
    : m_sound_write_idx(0)
    , m_round_number(0)
    , m_score_t(0)
    , m_score_ct(0)
    , m_bomb_state(BombState::NOT_PLANTED)
    , m_freeze_time(false)
    , m_round_start_time(0.0) {
    std::memset(m_bomb_position, 0, sizeof(m_bomb_position));
    std::memset(m_sound_buffer, 0, sizeof(m_sound_buffer));
}

GameState Perception::extract_state(int bot_index, uint32_t tick, double timestamp) {
    GameState state;
    state.clear();

    state.tick = tick;
    state.timestamp = timestamp;
    state.bot_index = static_cast<uint32_t>(bot_index);

    // In a real implementation, these would be extracted from the engine's
    // entity list using the HLSDK/MetaMod API:
    //
    // edict_t* bot_edict = INDEXENT(bot_entity_index);
    // entvars_t* pev = &bot_edict->v;
    //
    // state.position = pev->origin;
    // state.velocity = pev->velocity;
    // state.view_angles = pev->v_angle;
    // state.health = pev->health;
    // state.armor = pev->armorvalue;
    // state.is_alive = pev->deadflag == DEAD_NO;
    // state.is_on_ground = (pev->flags & FL_ONGROUND) != 0;
    // state.is_crouching = (pev->flags & FL_DUCKING) != 0;
    //
    // Weapon info would come from:
    // CBasePlayerWeapon* weapon = bot->m_pActiveItem;
    // state.current_weapon = weapon->m_iId;
    // state.ammo_clip = weapon->m_iClip;
    //
    // For enemies, iterate through all players and check visibility:
    // for (int i = 1; i <= gpGlobals->maxClients; i++) {
    //     edict_t* player = INDEXENT(i);
    //     if (is_enemy(bot, player) && is_visible(bot_origin, player_origin)) {
    //         state.enemies[state.num_enemies++] = extract_player_info(bot, player);
    //     }
    // }

    // Round context from tracked state
    state.round_number = static_cast<uint32_t>(m_round_number);
    state.bomb_state = static_cast<int32_t>(m_bomb_state);
    std::memcpy(state.bomb_position, m_bomb_position, sizeof(float) * 3);
    state.score_t = static_cast<uint32_t>(m_score_t);
    state.score_ct = static_cast<uint32_t>(m_score_ct);
    state.freeze_time = m_freeze_time ? 1 : 0;

    if (m_round_start_time > 0.0) {
        state.round_time = static_cast<float>(timestamp - m_round_start_time);
    }

    // Process recent sounds
    state.num_sounds = 0;
    for (int i = 0; i < MAX_SOUND_RECORDS && state.num_sounds < MAX_SOUNDS; i++) {
        int idx = (m_sound_write_idx - 1 - i + MAX_SOUND_RECORDS) % MAX_SOUND_RECORDS;
        const auto& snd = m_sound_buffer[idx];

        if (snd.type == SoundType::NONE) continue;

        double age = timestamp - snd.timestamp;
        if (age > 5.0) continue;  // ignore sounds older than 5 seconds

        SoundEvent& evt = state.sounds[state.num_sounds];

        // Compute direction from bot to sound
        // (In real implementation, use bot's position)
        evt.direction[0] = snd.origin[0] - state.position[0];
        evt.direction[1] = snd.origin[1] - state.position[1];
        evt.direction[2] = snd.origin[2] - state.position[2];

        // Normalize direction
        float len = std::sqrt(
            evt.direction[0] * evt.direction[0] +
            evt.direction[1] * evt.direction[1] +
            evt.direction[2] * evt.direction[2]
        );
        if (len > 0.01f) {
            evt.direction[0] /= len;
            evt.direction[1] /= len;
            evt.direction[2] /= len;
        }

        evt.sound_type = static_cast<uint32_t>(snd.type);
        evt.time_ago = static_cast<float>(age);
        evt.volume = snd.volume;

        state.num_sounds++;
    }

    return state;
}

void Perception::on_sound(const float origin[3], SoundType type, float volume) {
    auto& snd = m_sound_buffer[m_sound_write_idx];
    std::memcpy(snd.origin, origin, sizeof(float) * 3);
    snd.type = type;
    snd.volume = volume;
    snd.timestamp = 0.0;  // would use engine time in real implementation

    m_sound_write_idx = (m_sound_write_idx + 1) % MAX_SOUND_RECORDS;
}

void Perception::on_round_start() {
    m_round_number++;
    m_bomb_state = BombState::NOT_PLANTED;
    std::memset(m_bomb_position, 0, sizeof(m_bomb_position));
    m_freeze_time = true;
    m_round_start_time = 0.0;  // set to engine time in real implementation

    // Clear sound buffer
    std::memset(m_sound_buffer, 0, sizeof(m_sound_buffer));
    m_sound_write_idx = 0;
}

void Perception::on_round_end(Team winner) {
    if (winner == Team::TERRORIST) {
        m_score_t++;
    } else if (winner == Team::CT) {
        m_score_ct++;
    }
}

void Perception::on_bomb_planted(const float position[3]) {
    m_bomb_state = BombState::PLANTED;
    std::memcpy(m_bomb_position, position, sizeof(float) * 3);
}

void Perception::on_bomb_defused() {
    m_bomb_state = BombState::DEFUSED;
}

void Perception::on_bomb_exploded() {
    m_bomb_state = BombState::EXPLODED;
}

bool Perception::is_visible(const float from[3], const float to[3]) const {
    // In real implementation, use engine's TraceLine:
    //
    // TraceResult tr;
    // TRACE_LINE(from, to, ignore_monsters, pentIgnore, &tr);
    // return tr.flFraction >= 1.0f;

    (void)from;
    (void)to;
    return true;  // placeholder
}

void Perception::find_nearest_waypoints(
    const float pos[3], int32_t* out_waypoints, int max_count
) {
    // Would use Navigation::find_k_nearest in real implementation
    (void)pos;
    for (int i = 0; i < max_count; i++) {
        out_waypoints[i] = -1;
    }
}

}  // namespace neurbot
