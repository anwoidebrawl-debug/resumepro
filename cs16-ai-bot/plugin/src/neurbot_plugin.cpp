/**
 * @file neurbot_plugin.cpp
 * @brief NeurBot MetaMod plugin entry point.
 *
 * Implements the MetaMod plugin interface:
 * - GiveFnptrsToDll: receives engine function pointers
 * - Meta_Query: provides plugin info
 * - Meta_Attach: initializes the plugin
 * - Meta_Detach: shuts down the plugin
 *
 * On each server frame, the plugin:
 * 1. Extracts game state via the Perception module
 * 2. Writes states to shared memory for the Python engine
 * 3. Reads neural actions from shared memory
 * 4. Executes actions via the ActionExecutor
 */

#include "neurbot_plugin.h"
#include "bot_manager.h"

#include <cstdio>
#include <cstring>

namespace neurbot {

// Global state
static bool g_plugin_active = false;
static float g_last_frame_time = 0.0f;

bool plugin_init() {
    printf("[NeurBot] Initializing v%s by %s\n", PLUGIN_VERSION, PLUGIN_AUTHOR);

    // Initialize bot manager with shared memory IPC
    if (!BotManager::instance().init("/neurbot_state", MAX_BOTS)) {
        printf("[NeurBot] ERROR: Failed to initialize bot manager\n");
        return false;
    }

    g_plugin_active = true;
    printf("[NeurBot] Plugin initialized successfully\n");
    return true;
}

void plugin_shutdown() {
    if (!g_plugin_active) return;

    printf("[NeurBot] Shutting down...\n");
    BotManager::instance().shutdown();
    g_plugin_active = false;
    printf("[NeurBot] Shutdown complete\n");
}

void plugin_frame() {
    if (!g_plugin_active) return;

    // Compute frame time (simplified - real implementation would use engine time)
    float frametime = 1.0f / 64.0f;  // assume 64 tick
    BotManager::instance().frame(frametime);
}

}  // namespace neurbot

// ============================================================================
// MetaMod Plugin Interface (C linkage)
// ============================================================================

/*
 * In a real build, these functions would use the actual MetaMod SDK types.
 * Here we provide the structure that MetaMod expects.
 *
 * The plugin is loaded by MetaMod as a shared library. MetaMod calls these
 * exported functions to integrate the plugin into the engine's call chain.
 *
 * Build note: Compile with -shared -fPIC on Linux.
 */

extern "C" {

// Plugin info structure (MetaMod format)
struct plugin_info_t {
    const char* ifvers;
    const char* name;
    const char* version;
    const char* date;
    const char* author;
    const char* url;
    const char* logtag;
    int loadable;
    int unloadable;
};

static plugin_info_t g_plugin_info = {
    "5:13",                          // interface version
    neurbot::PLUGIN_NAME,
    neurbot::PLUGIN_VERSION,
    neurbot::PLUGIN_DATE,
    neurbot::PLUGIN_AUTHOR,
    neurbot::PLUGIN_URL,
    "NEURBOT",                       // log tag
    0x10,                            // loadable: after game init
    0x10,                            // unloadable: at any time
};

/**
 * Meta_Query - Called by MetaMod to get plugin info.
 */
int Meta_Query(const char* /*ifvers*/, plugin_info_t** pinfo, void* /*pMetaUtilFuncs*/) {
    *pinfo = &g_plugin_info;
    return 1;  // TRUE
}

/**
 * Meta_Attach - Called when MetaMod activates the plugin.
 */
int Meta_Attach(int /*now*/, void* /*pFunctionTable*/, void* /*pMGlobals*/, void* /*pGamedllFuncs*/) {
    return neurbot::plugin_init() ? 1 : 0;
}

/**
 * Meta_Detach - Called when MetaMod deactivates the plugin.
 */
int Meta_Detach(int /*now*/, int /*reason*/) {
    neurbot::plugin_shutdown();
    return 1;
}

/**
 * GiveFnptrsToDll - Receives engine function pointers.
 */
void GiveFnptrsToDll(void* /*pengfuncsFromEngine*/, void* /*pGlobals*/) {
    // Store engine function pointers for later use
    // In real implementation, these would be cast to enginefuncs_t*
}

}  // extern "C"
