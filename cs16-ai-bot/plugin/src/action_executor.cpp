/**
 * @file action_executor.cpp
 * @brief Translates neural actions to engine commands.
 */

#include "action_executor.h"
#include <cmath>
#include <cstdio>
#include <algorithm>

namespace neurbot {

// CS 1.6 movement constants
static constexpr float MAX_SPEED = 250.0f;      // cl_forwardspeed
static constexpr float CROUCH_SPEED = 125.0f;    // crouched speed
static constexpr float MAX_PITCH = 89.0f;
static constexpr float MIN_PITCH = -89.0f;

ActionExecutor::ActionExecutor() {
    for (auto& state : m_bot_states) {
        state.clear();
    }
}

void ActionExecutor::execute(int bot_index, const BotAction& action, float frametime) {
    if (bot_index < 0 || bot_index >= MAX_BOTS) return;

    auto& state = m_bot_states[bot_index];

    // 1. Apply aim changes
    apply_aim(bot_index, action.aim_delta_pitch, action.aim_delta_yaw);

    // 2. Compute movement speeds
    float forward_speed = 0.0f;
    float side_speed = 0.0f;
    compute_move_speeds(
        action.move_forward, action.move_right,
        action.crouch != 0,
        &forward_speed, &side_speed
    );

    // 3. Build button flags
    int buttons = build_buttons(action);

    // 4. Handle weapon switching
    if (action.weapon_slot > 0 && action.weapon_slot <= 5) {
        if (state.current_weapon_slot != static_cast<int>(action.weapon_slot)) {
            state.current_weapon_slot = static_cast<int>(action.weapon_slot);
            // In real implementation:
            // FakeClientCommand(bot_edict, "slot%d", action.weapon_slot);
        }
    }

    // 5. Handle buy commands
    if (action.buy_command > 0 && state.is_buying) {
        execute_buy(bot_index, action.buy_command);
    }

    // 6. Execute movement via engine
    // In real implementation:
    //
    // g_engfuncs.pfnRunPlayerMove(
    //     bot_edict,
    //     state.view_angles,      // view angles
    //     forward_speed,           // forward move
    //     side_speed,              // side move
    //     0.0f,                    // up move
    //     buttons,                 // button flags
    //     0,                       // impulse
    //     static_cast<unsigned char>(frametime * 1000.0f)  // msec
    // );

    (void)frametime;  // used in real implementation
}

void ActionExecutor::execute_buy(int bot_index, uint32_t buy_command) {
    if (bot_index < 0 || bot_index >= MAX_BOTS) return;

    // Buy command mapping (simplified)
    // In real implementation, issue FakeClientCommand with buy menu selections
    //
    // Common buy commands:
    //  1: Primary weapon menu
    //  2: Pistol menu
    //  3: Armor
    //  4: Grenades
    //  5: Defuse kit
    //
    // Specific weapons (by ID):
    // AK47=15, M4A1=16, AWP=20, etc.
    //
    // Example:
    // FakeClientCommand(bot_edict, "buy");
    // FakeClientCommand(bot_edict, "menuselect 4");  // rifles
    // FakeClientCommand(bot_edict, "menuselect 1");  // first rifle

    const char* buy_cmds[] = {
        "",              // 0: no buy
        "vest",          // 1: kevlar
        "vesthelm",      // 2: kevlar + helmet
        "defuser",       // 3: defuse kit
        "hegren",        // 4: HE grenade
        "flash",         // 5: flashbang
        "sgren",         // 6: smoke grenade
        "ak47",          // 7: AK-47
        "m4a1",          // 8: M4A1
        "awp",           // 9: AWP
        "deagle",        // 10: Desert Eagle
        "mp5",           // 11: MP5
        "famas",         // 12: FAMAS
        "galil",         // 13: Galil
        "p90",           // 14: P90
        "scout",         // 15: Scout
    };

    if (buy_command < sizeof(buy_cmds) / sizeof(buy_cmds[0])) {
        // FakeClientCommand(bot_edict, buy_cmds[buy_command]);
        (void)buy_cmds;
    }
}

void ActionExecutor::reset(int bot_index) {
    if (bot_index >= 0 && bot_index < MAX_BOTS) {
        m_bot_states[bot_index].clear();
        m_bot_states[bot_index].is_buying = true;  // can buy at round start
    }
}

void ActionExecutor::compute_move_speeds(
    float forward, float right, bool is_crouching,
    float* out_forward_speed, float* out_side_speed
) {
    float max_spd = is_crouching ? CROUCH_SPEED : MAX_SPEED;

    *out_forward_speed = std::clamp(forward, -1.0f, 1.0f) * max_spd;
    *out_side_speed = std::clamp(right, -1.0f, 1.0f) * max_spd;

    // Normalize diagonal movement
    float total_sq = (*out_forward_speed) * (*out_forward_speed) +
                     (*out_side_speed) * (*out_side_speed);
    float max_sq = max_spd * max_spd;

    if (total_sq > max_sq) {
        float scale = max_spd / std::sqrt(total_sq);
        *out_forward_speed *= scale;
        *out_side_speed *= scale;
    }
}

void ActionExecutor::apply_aim(int bot_index, float delta_pitch, float delta_yaw) {
    auto& state = m_bot_states[bot_index];

    state.view_pitch += delta_pitch;
    state.view_yaw += delta_yaw;

    // Clamp pitch
    state.view_pitch = std::clamp(state.view_pitch, MIN_PITCH, MAX_PITCH);

    // Normalize yaw to [0, 360)
    while (state.view_yaw < 0.0f) state.view_yaw += 360.0f;
    while (state.view_yaw >= 360.0f) state.view_yaw -= 360.0f;
}

int ActionExecutor::build_buttons(const BotAction& action) {
    int buttons = 0;

    if (action.fire)   buttons |= IN_ATTACK;
    if (action.fire2)  buttons |= IN_ATTACK2;
    if (action.jump)   buttons |= IN_JUMP;
    if (action.crouch) buttons |= IN_DUCK;
    if (action.reload) buttons |= IN_RELOAD;
    if (action.use)    buttons |= IN_USE;

    // Movement buttons (for compatibility with some game mechanics)
    if (action.move_forward > 0.3f)  buttons |= IN_FORWARD;
    if (action.move_forward < -0.3f) buttons |= IN_BACK;
    if (action.move_right > 0.3f)    buttons |= IN_MOVERIGHT;
    if (action.move_right < -0.3f)   buttons |= IN_MOVELEFT;

    return buttons;
}

}  // namespace neurbot
