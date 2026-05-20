/**
 * @file neurbot_plugin.h
 * @brief NeurBot MetaMod plugin - main header.
 *
 * This plugin integrates with the Half-Life Dedicated Server via MetaMod
 * to provide human-like AI bots powered by neural network inference.
 */

#pragma once

#include "protocol.h"

// Forward declarations for HL SDK types (minimal)
// In a real build these come from the HLSDK headers

#ifndef HLSDK_TYPES_DEFINED
#define HLSDK_TYPES_DEFINED

typedef float vec_t;
typedef vec_t vec3_t[3];

typedef struct edict_s edict_t;
typedef struct entvars_s entvars_t;

// Minimal engine function typedefs
typedef unsigned int string_t;

#define MAX_PLAYERS 32
#define FL_ONGROUND (1 << 9)
#define FL_DUCKING (1 << 14)

// Input buttons
#define IN_ATTACK     (1 << 0)
#define IN_JUMP       (1 << 1)
#define IN_DUCK       (1 << 2)
#define IN_FORWARD    (1 << 3)
#define IN_BACK       (1 << 4)
#define IN_USE        (1 << 5)
#define IN_MOVELEFT   (1 << 9)
#define IN_MOVERIGHT  (1 << 10)
#define IN_ATTACK2    (1 << 11)
#define IN_RELOAD     (1 << 13)

#endif  // HLSDK_TYPES_DEFINED

namespace neurbot {

/**
 * Plugin version info.
 */
constexpr const char* PLUGIN_NAME = "NeurBot";
constexpr const char* PLUGIN_VERSION = "0.1.0";
constexpr const char* PLUGIN_AUTHOR = "NeurBot Team";
constexpr const char* PLUGIN_URL = "https://github.com/neurbot/cs16-ai-bot";
constexpr const char* PLUGIN_DATE = __DATE__;

/**
 * Initialize the plugin. Called by MetaMod on load.
 */
bool plugin_init();

/**
 * Shutdown the plugin. Called by MetaMod on unload.
 */
void plugin_shutdown();

/**
 * Called every server frame (tick).
 * This is where we extract game state and apply neural actions.
 */
void plugin_frame();

}  // namespace neurbot
