/**
 * @file bot_manager.cpp
 * @brief Bot lifecycle management and main perception/action loop.
 */

#include "bot_manager.h"
#include <cstdio>
#include <cstring>
#include <cmath>

namespace neurbot {

BotManager& BotManager::instance() {
    static BotManager s_instance;
    return s_instance;
}

bool BotManager::init(const char* shm_name, int max_bots) {
    if (m_initialized) return true;

    m_max_bots = max_bots < MAX_BOTS ? max_bots : MAX_BOTS;

    for (auto& bot : m_bots) {
        bot.clear();
    }

    // Initialize IPC
    if (!m_ipc.init(shm_name)) {
        printf("[NeurBot] Failed to initialize IPC bridge\n");
        return false;
    }

    m_tick = 0;
    m_active_bots = 0;
    m_fallback_mode = false;
    m_initialized = true;

    printf("[NeurBot] Bot manager initialized (max_bots=%d)\n", m_max_bots);
    return true;
}

void BotManager::shutdown() {
    if (!m_initialized) return;

    // Remove all bots
    for (int i = 0; i < MAX_BOTS; i++) {
        if (m_bots[i].active) {
            remove_bot(i);
        }
    }

    m_ipc.shutdown();
    m_initialized = false;

    printf("[NeurBot] Bot manager shut down\n");
}

void BotManager::frame(float frametime) {
    if (!m_initialized || m_active_bots == 0) return;

    m_tick++;

    // Check if Python engine is connected
    bool engine_connected = m_ipc.is_engine_connected();

    if (!engine_connected && !m_fallback_mode) {
        printf("[NeurBot] Python engine not connected, using fallback AI\n");
        m_fallback_mode = true;
    } else if (engine_connected && m_fallback_mode) {
        printf("[NeurBot] Python engine connected, switching to neural AI\n");
        m_fallback_mode = false;
    }

    // Phase 1: Extract game state for all active bots
    GameState states[MAX_BOTS];
    int state_count = 0;

    for (int i = 0; i < MAX_BOTS; i++) {
        if (!m_bots[i].active) continue;

        double timestamp = static_cast<double>(m_tick) / 64.0;
        states[state_count] = m_perception.extract_state(i, m_tick, timestamp);
        state_count++;
    }

    if (m_fallback_mode) {
        // Fallback: use simple rule-based AI
        int idx = 0;
        for (int i = 0; i < MAX_BOTS; i++) {
            if (!m_bots[i].active) continue;
            execute_fallback(i, states[idx], frametime);
            idx++;
        }
        return;
    }

    // Phase 2: Write states to shared memory
    m_ipc.write_states(states, state_count);

    // Phase 3: Read actions from Python engine
    BotAction actions[MAX_BOTS];
    int action_count = m_ipc.read_actions(actions, state_count);

    // Phase 4: Execute actions
    if (action_count > 0) {
        int idx = 0;
        for (int i = 0; i < MAX_BOTS && idx < action_count; i++) {
            if (!m_bots[i].active) continue;
            m_executor.execute(i, actions[idx], frametime);
            idx++;
        }
    }
}

int BotManager::add_bot(const char* name) {
    if (m_active_bots >= m_max_bots) {
        printf("[NeurBot] Cannot add bot: maximum reached (%d)\n", m_max_bots);
        return -1;
    }

    // Find free slot
    int slot = -1;
    for (int i = 0; i < MAX_BOTS; i++) {
        if (!m_bots[i].active) {
            slot = i;
            break;
        }
    }

    if (slot < 0) return -1;

    m_bots[slot].active = true;
    strncpy(m_bots[slot].name, name, sizeof(m_bots[slot].name) - 1);
    m_bots[slot].name[sizeof(m_bots[slot].name) - 1] = '\0';

    // In real implementation:
    // edict_t* bot_edict = (*g_engfuncs.pfnCreateFakeClient)(name);
    // m_bots[slot].entity_index = ENTINDEX(bot_edict);

    m_active_bots++;
    m_executor.reset(slot);

    printf("[NeurBot] Added bot '%s' at slot %d (total: %d)\n",
           name, slot, m_active_bots);
    return slot;
}

void BotManager::remove_bot(int index) {
    if (index < 0 || index >= MAX_BOTS || !m_bots[index].active) return;

    printf("[NeurBot] Removing bot '%s' from slot %d\n", m_bots[index].name, index);

    // In real implementation:
    // SERVER_COMMAND(UTIL_VarArgs("kick \"%s\"\n", m_bots[index].name));

    m_bots[index].clear();
    m_active_bots--;
}

void BotManager::on_round_start() {
    m_perception.on_round_start();

    for (int i = 0; i < MAX_BOTS; i++) {
        if (m_bots[i].active) {
            m_executor.reset(i);
        }
    }
}

void BotManager::on_round_end(Team winner) {
    m_perception.on_round_end(winner);
}

void BotManager::on_sound(const float origin[3], SoundType type, float volume) {
    m_perception.on_sound(origin, type, volume);
}

void BotManager::on_bomb_planted(const float pos[3]) {
    m_perception.on_bomb_planted(pos);
}

void BotManager::on_bomb_defused() {
    m_perception.on_bomb_defused();
}

void BotManager::on_bomb_exploded() {
    m_perception.on_bomb_exploded();
}

void BotManager::execute_fallback(
    int bot_index, const GameState& state, float frametime
) {
    // Simple fallback AI: move forward, look around, shoot visible enemies
    BotAction action;
    action.clear();

    if (!state.is_alive) return;

    // Move forward
    action.move_forward = 0.8f;

    // Slight random strafing
    float t = static_cast<float>(m_tick) * 0.1f;
    action.move_right = std::sin(t) * 0.3f;

    // Look around slowly
    action.aim_delta_yaw = std::sin(t * 0.3f) * 1.0f;

    // If enemies visible, aim and shoot
    if (state.num_enemies > 0) {
        const auto& enemy = state.enemies[0];
        if (enemy.visible && enemy.alive) {
            // Aim toward enemy (simplified)
            float dx = enemy.relative_pos[0];
            float dy = enemy.relative_pos[1];
            float dz = enemy.relative_pos[2];

            float dist_h = std::sqrt(dx * dx + dy * dy);
            if (dist_h > 0.01f) {
                float target_yaw = std::atan2(dy, dx) * 180.0f / 3.14159f;
                float target_pitch = std::atan2(-dz, dist_h) * 180.0f / 3.14159f;

                action.aim_delta_yaw = target_yaw * 0.1f;  // smooth aim
                action.aim_delta_pitch = target_pitch * 0.1f;
            }

            action.fire = 1;
        }
    }

    m_executor.execute(bot_index, action, frametime);
}

}  // namespace neurbot
