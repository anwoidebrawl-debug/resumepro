/**
 * @file ipc_bridge.cpp
 * @brief Implementation of shared memory IPC bridge.
 */

#include "ipc_bridge.h"
#include <cstdio>
#include <cstring>

#ifdef _WIN32
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

namespace neurbot {

// Total shared memory size
static constexpr size_t TOTAL_SHM_SIZE =
    SHM_HEADER_SIZE +
    SHM_STATE_HEADER_SIZE + (SHM_STATE_SIZE_PER_BOT * MAX_BOTS) +
    SHM_ACTION_HEADER_SIZE + (SHM_ACTION_SIZE_PER_BOT * MAX_BOTS);

IPCBridge::IPCBridge()
    : m_shm_ptr(nullptr)
    , m_shm_fd(-1)
    , m_state_seq(0)
    , m_last_action_seq(0)
    , m_initialized(false) {
}

IPCBridge::~IPCBridge() {
    shutdown();
}

bool IPCBridge::init(const char* shm_name) {
    if (m_initialized) {
        return true;
    }

#ifdef _WIN32
    // Windows: CreateFileMapping
    HANDLE hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE,
        0, TOTAL_SHM_SIZE, shm_name);

    if (hMapFile == nullptr) {
        printf("[NeurBot IPC] Failed to create file mapping\n");
        return false;
    }

    m_shm_ptr = MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, TOTAL_SHM_SIZE);
    if (m_shm_ptr == nullptr) {
        CloseHandle(hMapFile);
        printf("[NeurBot IPC] Failed to map view of file\n");
        return false;
    }
#else
    // Linux: /dev/shm
    char shm_path[256];
    snprintf(shm_path, sizeof(shm_path), "/dev/shm%s", shm_name);

    m_shm_fd = open(shm_path, O_RDWR, 0666);
    if (m_shm_fd < 0) {
        // Try creating it
        m_shm_fd = open(shm_path, O_CREAT | O_RDWR, 0666);
        if (m_shm_fd < 0) {
            printf("[NeurBot IPC] Failed to open shared memory: %s\n", shm_path);
            return false;
        }
        if (ftruncate(m_shm_fd, TOTAL_SHM_SIZE) < 0) {
            printf("[NeurBot IPC] Failed to set shared memory size\n");
            close(m_shm_fd);
            m_shm_fd = -1;
            return false;
        }
    }

    m_shm_ptr = mmap(nullptr, TOTAL_SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, m_shm_fd, 0);
    if (m_shm_ptr == MAP_FAILED) {
        printf("[NeurBot IPC] Failed to mmap shared memory\n");
        close(m_shm_fd);
        m_shm_fd = -1;
        m_shm_ptr = nullptr;
        return false;
    }
#endif

    // Initialize or verify header
    auto* header = static_cast<ShmHeader*>(m_shm_ptr);

    if (header->magic != MAGIC_NUMBER) {
        // First initialization
        header->magic = MAGIC_NUMBER;
        header->version = PROTOCOL_VERSION;
        header->state_offset = SHM_HEADER_SIZE;
        header->action_offset = SHM_HEADER_SIZE + SHM_STATE_HEADER_SIZE +
                                (SHM_STATE_SIZE_PER_BOT * MAX_BOTS);

        // Clear state and action regions
        std::memset(
            static_cast<char*>(m_shm_ptr) + header->state_offset,
            0, SHM_STATE_HEADER_SIZE + (SHM_STATE_SIZE_PER_BOT * MAX_BOTS)
        );
        std::memset(
            static_cast<char*>(m_shm_ptr) + header->action_offset,
            0, SHM_ACTION_HEADER_SIZE + (SHM_ACTION_SIZE_PER_BOT * MAX_BOTS)
        );

        printf("[NeurBot IPC] Created shared memory (size=%zu bytes)\n", TOTAL_SHM_SIZE);
    } else {
        printf("[NeurBot IPC] Connected to existing shared memory\n");
    }

    m_initialized = true;
    return true;
}

void IPCBridge::write_states(const GameState* states, int count) {
    if (!m_initialized || m_shm_ptr == nullptr) return;

    auto* header = static_cast<ShmHeader*>(m_shm_ptr);
    auto* base = static_cast<char*>(m_shm_ptr) + header->state_offset;
    auto* state_header = reinterpret_cast<StateRegionHeader*>(base);

    // Set lock
    state_header->lock = 1;

    // Write bot count
    state_header->bot_count = static_cast<uint32_t>(count);

    // Write each bot's state
    char* data_ptr = base + SHM_STATE_HEADER_SIZE;
    for (int i = 0; i < count && i < MAX_BOTS; i++) {
        std::memcpy(data_ptr + (i * SHM_STATE_SIZE_PER_BOT), &states[i], sizeof(GameState));
    }

    // Increment sequence and release lock
    m_state_seq++;
    state_header->sequence = m_state_seq;
    state_header->lock = 0;
}

int IPCBridge::read_actions(BotAction* actions, int max_count) {
    if (!m_initialized || m_shm_ptr == nullptr) return 0;

    auto* header = static_cast<ShmHeader*>(m_shm_ptr);
    auto* base = static_cast<char*>(m_shm_ptr) + header->action_offset;
    auto* action_header = reinterpret_cast<ActionRegionHeader*>(base);

    // Check lock
    if (action_header->lock != 0) return 0;

    // Check for new data
    if (action_header->sequence <= m_last_action_seq) return 0;

    m_last_action_seq = action_header->sequence;

    // Read actions
    char* data_ptr = base + SHM_ACTION_HEADER_SIZE;
    int count = max_count < MAX_BOTS ? max_count : MAX_BOTS;

    for (int i = 0; i < count; i++) {
        std::memcpy(&actions[i], data_ptr + (i * SHM_ACTION_SIZE_PER_BOT), sizeof(BotAction));
    }

    return count;
}

bool IPCBridge::is_engine_connected() const {
    if (!m_initialized || m_shm_ptr == nullptr) return false;

    auto* header = static_cast<const ShmHeader*>(m_shm_ptr);
    auto* base = static_cast<const char*>(m_shm_ptr) + header->action_offset;
    auto* action_header = reinterpret_cast<const ActionRegionHeader*>(base);

    // Consider engine connected if we've received actions recently
    return action_header->sequence > 0;
}

void IPCBridge::shutdown() {
    if (!m_initialized) return;

#ifdef _WIN32
    if (m_shm_ptr != nullptr) {
        UnmapViewOfFile(m_shm_ptr);
        m_shm_ptr = nullptr;
    }
#else
    if (m_shm_ptr != nullptr && m_shm_ptr != MAP_FAILED) {
        munmap(m_shm_ptr, TOTAL_SHM_SIZE);
        m_shm_ptr = nullptr;
    }
    if (m_shm_fd >= 0) {
        close(m_shm_fd);
        m_shm_fd = -1;
    }
#endif

    m_initialized = false;
    printf("[NeurBot IPC] Shared memory released\n");
}

}  // namespace neurbot
