/**
 * @file perception.h
 * @brief Game state extraction (perception) module.
 *
 * Hooks into engine functions to extract complete game state:
 * - Player positions, velocities, health, armor
 * - Weapon states, ammo counts
 * - Visibility checks (TraceLine)
 * - Sound events
 * - Round state, economy, bomb status
 */

#pragma once

#include "protocol.h"

namespace neurbot {

class Perception {
public:
    Perception();

    /**
     * Extract complete game state for a specific bot.
     * @param bot_index Index of the bot (0-based)
     * @param tick Current server tick
     * @param timestamp Current server time
     * @return Filled GameState structure
     */
    GameState extract_state(int bot_index, uint32_t tick, double timestamp);

    /**
     * Register a sound event for processing.
     * @param origin Sound origin position
     * @param type Type of sound
     * @param volume Sound volume
     */
    void on_sound(const float origin[3], SoundType type, float volume);

    /**
     * Called when a new round starts.
     */
    void on_round_start();

    /**
     * Called when the round ends.
     * @param winner Winning team
     */
    void on_round_end(Team winner);

    /**
     * Update bomb state.
     */
    void on_bomb_planted(const float position[3]);
    void on_bomb_defused();
    void on_bomb_exploded();

private:
    /**
     * Perform visibility check between two points using engine TraceLine.
     */
    bool is_visible(const float from[3], const float to[3]) const;

    /**
     * Find nearest navigation waypoints to a position.
     */
    void find_nearest_waypoints(const float pos[3], int32_t* out_waypoints, int max_count);

    // Sound event buffer
    struct SoundRecord {
        float origin[3];
        SoundType type;
        float volume;
        double timestamp;
    };

    static constexpr int MAX_SOUND_RECORDS = 32;
    SoundRecord m_sound_buffer[MAX_SOUND_RECORDS];
    int m_sound_write_idx;

    // Round state
    int m_round_number;
    int m_score_t;
    int m_score_ct;
    BombState m_bomb_state;
    float m_bomb_position[3];
    bool m_freeze_time;
    double m_round_start_time;
};

}  // namespace neurbot
