/**
 * @file bot_manager.h
 * @brief Manages bot instances and coordinates perception/action cycle.
 */

#pragma once

#include "protocol.h"
#include "perception.h"
#include "action_executor.h"
#include "ipc_bridge.h"

namespace neurbot {

class BotManager {
public:
    static BotManager& instance();

    /**
     * Initialize the bot manager.
     * @param shm_name Shared memory name for IPC
     * @param max_bots Maximum number of bots
     * @return true on success
     */
    bool init(const char* shm_name, int max_bots);

    /**
     * Shutdown and cleanup.
     */
    void shutdown();

    /**
     * Called every server frame.
     * Extracts game state, sends to Python, reads actions, executes.
     */
    void frame(float frametime);

    /**
     * Add a bot to the server.
     * @param name Bot name
     * @return Bot index, or -1 on failure
     */
    int add_bot(const char* name);

    /**
     * Remove a bot from the server.
     * @param index Bot index
     */
    void remove_bot(int index);

    /**
     * Get number of active bots.
     */
    int get_bot_count() const { return m_active_bots; }

    // Event handlers
    void on_round_start();
    void on_round_end(Team winner);
    void on_sound(const float origin[3], SoundType type, float volume);
    void on_bomb_planted(const float pos[3]);
    void on_bomb_defused();
    void on_bomb_exploded();

private:
    BotManager() = default;
    BotManager(const BotManager&) = delete;
    BotManager& operator=(const BotManager&) = delete;

    struct BotSlot {
        bool active;
        int entity_index;  // HLDS entity index
        char name[64];

        void clear() {
            active = false;
            entity_index = -1;
            name[0] = '\0';
        }
    };

    IPCBridge m_ipc;
    Perception m_perception;
    ActionExecutor m_executor;

    BotSlot m_bots[MAX_BOTS];
    int m_active_bots = 0;
    int m_max_bots = 5;
    uint32_t m_tick = 0;

    bool m_initialized = false;

    // Fallback mode when Python engine is not connected
    bool m_fallback_mode = false;
    void execute_fallback(int bot_index, const GameState& state, float frametime);
};

}  // namespace neurbot
