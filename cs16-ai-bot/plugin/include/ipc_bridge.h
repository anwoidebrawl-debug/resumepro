/**
 * @file ipc_bridge.h
 * @brief Shared memory IPC bridge for communicating with Python engine.
 */

#pragma once

#include "protocol.h"
#include <cstdint>

namespace neurbot {

class IPCBridge {
public:
    IPCBridge();
    ~IPCBridge();

    /**
     * Initialize shared memory region.
     * @param shm_name Name of the shared memory object (e.g., "/neurbot_state")
     * @return true on success
     */
    bool init(const char* shm_name);

    /**
     * Write game states for all active bots.
     * @param states Array of game states
     * @param count Number of bots
     */
    void write_states(const GameState* states, int count);

    /**
     * Read actions from Python engine.
     * @param actions Output array of actions
     * @param max_count Maximum number of actions to read
     * @return Number of actions read
     */
    int read_actions(BotAction* actions, int max_count);

    /**
     * Check if the Python engine is connected and responsive.
     */
    bool is_engine_connected() const;

    /**
     * Clean up shared memory.
     */
    void shutdown();

private:
    void* m_shm_ptr;       // Mapped shared memory
    int m_shm_fd;          // File descriptor
    uint32_t m_state_seq;  // State sequence counter
    uint32_t m_last_action_seq; // Last action sequence read
    bool m_initialized;
};

}  // namespace neurbot
