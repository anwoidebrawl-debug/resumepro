/**
 * @file action_executor.h
 * @brief Translates neural network actions into engine commands.
 *
 * Takes BotAction structures from the Python engine and converts them
 * into Half-Life engine commands (pfnRunPlayerMove, weapon switches, etc.)
 */

#pragma once

#include "protocol.h"

namespace neurbot {

class ActionExecutor {
public:
    ActionExecutor();

    /**
     * Execute a bot action by issuing engine commands.
     * @param bot_index Index of the bot
     * @param action Action to execute
     * @param frametime Time since last frame (seconds)
     */
    void execute(int bot_index, const BotAction& action, float frametime);

    /**
     * Execute a buy command during buy time.
     * @param bot_index Index of the bot
     * @param buy_command Buy command ID
     */
    void execute_buy(int bot_index, uint32_t buy_command);

    /**
     * Reset state for a bot (e.g., on round start).
     */
    void reset(int bot_index);

private:
    /**
     * Convert movement values to engine move speeds.
     */
    void compute_move_speeds(
        float forward, float right, bool is_crouching,
        float* out_forward_speed, float* out_side_speed
    );

    /**
     * Convert aim deltas to view angle changes.
     */
    void apply_aim(int bot_index, float delta_pitch, float delta_yaw);

    /**
     * Build button bitfield from action booleans.
     */
    int build_buttons(const BotAction& action);

    // Per-bot state
    struct BotExecutorState {
        float view_pitch;
        float view_yaw;
        int current_weapon_slot;
        bool is_buying;
        float buy_timer;

        void clear() {
            view_pitch = 0.0f;
            view_yaw = 0.0f;
            current_weapon_slot = 0;
            is_buying = false;
            buy_timer = 0.0f;
        }
    };

    BotExecutorState m_bot_states[MAX_BOTS];
};

}  // namespace neurbot
