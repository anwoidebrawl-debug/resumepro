/**
 * @file protocol.h
 * @brief Shared IPC protocol definitions between C++ plugin and Python engine.
 *
 * Defines the binary layout of structures exchanged via shared memory.
 * MUST be kept in sync with python/neurbot/ipc/protocol.py
 */

#pragma once

#include <cstdint>
#include <cstring>

namespace neurbot {

// Protocol constants
constexpr uint32_t MAGIC_NUMBER = 0x4E455552;  // "NEUR"
constexpr uint32_t PROTOCOL_VERSION = 1;
constexpr int MAX_ENEMIES = 5;
constexpr int MAX_TEAMMATES = 4;
constexpr int MAX_SOUNDS = 8;
constexpr int MAX_WAYPOINTS = 5;
constexpr int MAX_BOTS = 10;

// Shared memory layout
constexpr int SHM_HEADER_SIZE = 16;
constexpr int SHM_STATE_HEADER_SIZE = 9;
constexpr int SHM_ACTION_HEADER_SIZE = 5;
constexpr int SHM_STATE_SIZE_PER_BOT = 2048;
constexpr int SHM_ACTION_SIZE_PER_BOT = 64;

// Team IDs
enum class Team : int {
    UNASSIGNED = 0,
    TERRORIST = 1,
    CT = 2,
    SPECTATOR = 3,
};

// Weapon IDs (matches CS 1.6)
enum class WeaponID : int {
    NONE = 0, KNIFE = 1, USP = 2, GLOCK = 3, DEAGLE = 4,
    P228 = 5, ELITE = 6, FIVESEVEN = 7, M3 = 8, XM1014 = 9,
    MP5 = 10, TMP = 11, P90 = 12, MAC10 = 13, UMP45 = 14,
    AK47 = 15, M4A1 = 16, SG552 = 17, AUG = 18, SCOUT = 19,
    AWP = 20, G3SG1 = 21, SG550 = 22, GALIL = 23, FAMAS = 24,
    M249 = 25, SHIELD = 26, HE_GRENADE = 27, FLASHBANG = 28,
    SMOKE_GRENADE = 29, C4 = 30,
};

// Sound types
enum class SoundType : int {
    NONE = 0, FOOTSTEP = 1, GUNFIRE = 2, GRENADE_BOUNCE = 3,
    GRENADE_EXPLODE = 4, BOMB_PLANT = 5, BOMB_DEFUSE = 6,
    RELOAD = 7, SCREAM = 8,
};

// Bomb state
enum class BombState : int {
    NOT_PLANTED = 0, PLANTED = 1, DEFUSING = 2, EXPLODED = 3, DEFUSED = 4,
};

#pragma pack(push, 1)

/**
 * Information about a visible player (enemy or teammate).
 * Size: 40 bytes
 */
struct PlayerInfo {
    float relative_pos[3];     // relative position
    float velocity[3];         // velocity vector
    float health;              // estimated health
    float armor;               // estimated armor
    uint32_t weapon;           // weapon ID
    uint8_t visible;           // is currently visible
    uint8_t alive;             // is alive
    float time_since_seen;     // seconds since last seen
    float distance;            // distance to this player

    void clear() { std::memset(this, 0, sizeof(*this)); }
};

/**
 * A recent sound event.
 * Size: 24 bytes
 */
struct SoundEvent {
    float direction[3];        // normalized direction to sound
    uint32_t sound_type;       // SoundType enum
    float time_ago;            // seconds since sound occurred
    float volume;              // volume 0.0-1.0

    void clear() { std::memset(this, 0, sizeof(*this)); }
};

/**
 * Complete game state for a single bot.
 * Serialized to shared memory for Python engine consumption.
 */
struct GameState {
    // Header
    uint32_t tick;
    double timestamp;
    uint32_t bot_index;

    // Self state
    float position[3];
    float velocity[3];
    float view_angles[2];      // pitch, yaw
    float health;
    float armor;
    uint32_t money;
    uint32_t current_weapon;
    uint32_t ammo_clip;
    uint32_t ammo_reserve;
    uint8_t is_reloading;
    uint8_t is_scoped;
    uint8_t is_crouching;
    uint8_t is_on_ground;
    uint8_t is_alive;
    uint8_t _pad1;
    uint32_t team;

    // Enemies
    uint32_t num_enemies;
    PlayerInfo enemies[MAX_ENEMIES];

    // Teammates
    uint32_t num_teammates;
    PlayerInfo teammates[MAX_TEAMMATES];

    // Sounds
    uint32_t num_sounds;
    SoundEvent sounds[MAX_SOUNDS];

    // Round context
    float round_time;
    uint32_t round_number;
    int32_t bomb_state;
    float bomb_position[3];
    uint32_t score_t;
    uint32_t score_ct;
    uint8_t freeze_time;

    // Navigation
    int32_t nearest_waypoints[MAX_WAYPOINTS];
    uint32_t current_area;

    void clear() { std::memset(this, 0, sizeof(*this)); }
};

/**
 * Action output from Python engine, consumed by C++ action executor.
 */
struct BotAction {
    float move_forward;        // -1.0 to 1.0
    float move_right;          // -1.0 to 1.0
    float aim_delta_pitch;     // degrees
    float aim_delta_yaw;       // degrees
    uint8_t fire;
    uint8_t fire2;
    uint8_t jump;
    uint8_t crouch;
    uint8_t reload;
    uint8_t use;
    uint32_t weapon_slot;      // 0=no switch, 1-5
    uint32_t buy_command;      // 0=no buy, or command ID

    void clear() { std::memset(this, 0, sizeof(*this)); }
};

/**
 * Shared memory header.
 */
struct ShmHeader {
    uint32_t magic;
    uint32_t version;
    uint32_t state_offset;
    uint32_t action_offset;
};

/**
 * State region header.
 */
struct StateRegionHeader {
    uint8_t lock;
    uint32_t sequence;
    uint32_t bot_count;
};

/**
 * Action region header.
 */
struct ActionRegionHeader {
    uint8_t lock;
    uint32_t sequence;
};

#pragma pack(pop)

}  // namespace neurbot
