/**
 * @file navigation.cpp
 * @brief Navigation graph and A* pathfinding implementation.
 */

#include "navigation.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <queue>
#include <unordered_set>

namespace neurbot {

Navigation::Navigation() = default;

bool Navigation::load(const char* map_name, const char* nav_dir) {
    // Construct path to nav file
    char path[512];
    snprintf(path, sizeof(path), "%s/%s.nav", nav_dir, map_name);

    FILE* f = fopen(path, "rb");
    if (f == nullptr) {
        printf("[NeurBot Nav] Could not open: %s\n", path);
        return false;
    }

    // Read header
    uint32_t magic = 0;
    uint32_t version = 0;
    uint32_t node_count = 0;

    fread(&magic, sizeof(magic), 1, f);
    fread(&version, sizeof(version), 1, f);
    fread(&node_count, sizeof(node_count), 1, f);

    if (node_count == 0 || node_count > 10000) {
        printf("[NeurBot Nav] Invalid node count: %u\n", node_count);
        fclose(f);
        return false;
    }

    m_nodes.resize(node_count);

    // Read nodes
    for (uint32_t i = 0; i < node_count; i++) {
        auto& node = m_nodes[i];

        fread(node.position, sizeof(float), 3, f);
        fread(&node.radius, sizeof(float), 1, f);
        fread(&node.flags, sizeof(uint32_t), 1, f);

        // Read connections
        uint32_t num_connections = 0;
        fread(&num_connections, sizeof(uint32_t), 1, f);

        for (int j = 0; j < 8; j++) {
            node.connections[j] = -1;
            node.distances[j] = 0.0f;
        }

        for (uint32_t j = 0; j < num_connections && j < 8; j++) {
            int32_t target = 0;
            fread(&target, sizeof(int32_t), 1, f);
            node.connections[j] = target;

            // Compute distance
            if (target >= 0 && static_cast<uint32_t>(target) < node_count) {
                // Distance will be computed after all nodes are loaded
            }
        }
    }

    fclose(f);

    // Compute edge distances
    for (auto& node : m_nodes) {
        for (int j = 0; j < 8; j++) {
            if (node.connections[j] >= 0 &&
                static_cast<size_t>(node.connections[j]) < m_nodes.size()) {
                node.distances[j] = distance(
                    node.position,
                    m_nodes[node.connections[j]].position
                );
            }
        }
    }

    printf("[NeurBot Nav] Loaded %u nodes from %s\n", node_count, path);
    return true;
}

bool Navigation::find_path(
    const float from[3], const float to[3], std::vector<int>& path
) const {
    if (m_nodes.empty()) return false;

    int start = find_nearest(from);
    int goal = find_nearest(to);

    if (start < 0 || goal < 0) return false;
    if (start == goal) {
        path.push_back(start);
        return true;
    }

    // A* search
    struct AStarNode {
        int index;
        float f_cost;
        bool operator>(const AStarNode& other) const { return f_cost > other.f_cost; }
    };

    int n = static_cast<int>(m_nodes.size());
    std::vector<float> g_cost(n, 1e30f);
    std::vector<int> came_from(n, -1);
    std::unordered_set<int> closed;

    std::priority_queue<AStarNode, std::vector<AStarNode>, std::greater<AStarNode>> open;

    g_cost[start] = 0.0f;
    open.push({start, heuristic(start, goal)});

    while (!open.empty()) {
        auto current = open.top();
        open.pop();

        if (current.index == goal) {
            // Reconstruct path
            path.clear();
            int node = goal;
            while (node >= 0) {
                path.push_back(node);
                node = came_from[node];
            }
            std::reverse(path.begin(), path.end());
            return true;
        }

        if (closed.count(current.index)) continue;
        closed.insert(current.index);

        const auto& node = m_nodes[current.index];
        for (int j = 0; j < 8; j++) {
            int neighbor = node.connections[j];
            if (neighbor < 0 || closed.count(neighbor)) continue;

            float tentative_g = g_cost[current.index] + node.distances[j];
            if (tentative_g < g_cost[neighbor]) {
                g_cost[neighbor] = tentative_g;
                came_from[neighbor] = current.index;
                float f = tentative_g + heuristic(neighbor, goal);
                open.push({neighbor, f});
            }
        }
    }

    return false;  // no path found
}

int Navigation::find_nearest(const float pos[3]) const {
    if (m_nodes.empty()) return -1;

    int best = -1;
    float best_dist = 1e30f;

    for (int i = 0; i < static_cast<int>(m_nodes.size()); i++) {
        float d = distance(pos, m_nodes[i].position);
        if (d < best_dist) {
            best_dist = d;
            best = i;
        }
    }

    return best;
}

void Navigation::find_k_nearest(
    const float pos[3], int32_t* out_indices, int k
) const {
    // Simple brute force for small graphs
    struct DistIdx {
        float dist;
        int index;
        bool operator<(const DistIdx& other) const { return dist < other.dist; }
    };

    std::vector<DistIdx> all;
    all.reserve(m_nodes.size());

    for (int i = 0; i < static_cast<int>(m_nodes.size()); i++) {
        all.push_back({distance(pos, m_nodes[i].position), i});
    }

    std::partial_sort(
        all.begin(),
        all.begin() + std::min(k, static_cast<int>(all.size())),
        all.end()
    );

    for (int i = 0; i < k; i++) {
        if (i < static_cast<int>(all.size())) {
            out_indices[i] = all[i].index;
        } else {
            out_indices[i] = -1;
        }
    }
}

const NavNode* Navigation::get_node(int index) const {
    if (index < 0 || static_cast<size_t>(index) >= m_nodes.size()) {
        return nullptr;
    }
    return &m_nodes[index];
}

float Navigation::distance(const float a[3], const float b[3]) const {
    float dx = a[0] - b[0];
    float dy = a[1] - b[1];
    float dz = a[2] - b[2];
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

float Navigation::heuristic(int from, int to) const {
    return distance(m_nodes[from].position, m_nodes[to].position);
}

}  // namespace neurbot
