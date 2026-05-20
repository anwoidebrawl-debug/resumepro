/**
 * @file navigation.h
 * @brief Navigation graph (waypoint) system for bot pathfinding.
 *
 * Provides A* pathfinding on a pre-computed navigation graph.
 * Waypoints are loaded from .nav files compatible with YaPB format.
 */

#pragma once

#include <cstdint>
#include <vector>

namespace neurbot {

struct NavNode {
    float position[3];
    float radius;
    uint32_t flags;         // area type flags
    int32_t connections[8]; // indices of connected nodes (-1 = none)
    float distances[8];     // distances to connected nodes

    static constexpr uint32_t FLAG_NORMAL = 0;
    static constexpr uint32_t FLAG_CROUCH = 1 << 0;
    static constexpr uint32_t FLAG_LADDER = 1 << 1;
    static constexpr uint32_t FLAG_CAMP = 1 << 2;
    static constexpr uint32_t FLAG_BOMB_SITE = 1 << 3;
    static constexpr uint32_t FLAG_RESCUE = 1 << 4;
    static constexpr uint32_t FLAG_SNIPER = 1 << 5;
    static constexpr uint32_t FLAG_GOAL_T = 1 << 6;
    static constexpr uint32_t FLAG_GOAL_CT = 1 << 7;
};

class Navigation {
public:
    Navigation();

    /**
     * Load navigation graph from a .nav file.
     * @param map_name Name of the map (e.g., "de_dust2")
     * @param nav_dir Directory containing .nav files
     * @return true on success
     */
    bool load(const char* map_name, const char* nav_dir);

    /**
     * Find path between two positions using A*.
     * @param from Start position
     * @param to End position
     * @param path Output path (list of node indices)
     * @return true if path found
     */
    bool find_path(const float from[3], const float to[3], std::vector<int>& path) const;

    /**
     * Find nearest node to a position.
     * @param pos Position to search from
     * @return Node index, or -1 if no nodes
     */
    int find_nearest(const float pos[3]) const;

    /**
     * Find K nearest nodes to a position.
     */
    void find_k_nearest(const float pos[3], int32_t* out_indices, int k) const;

    /**
     * Get a node by index.
     */
    const NavNode* get_node(int index) const;

    /**
     * Get total number of nodes.
     */
    int node_count() const { return static_cast<int>(m_nodes.size()); }

    /**
     * Check if graph is loaded.
     */
    bool is_loaded() const { return !m_nodes.empty(); }

private:
    float distance(const float a[3], const float b[3]) const;
    float heuristic(int from, int to) const;

    std::vector<NavNode> m_nodes;
};

}  // namespace neurbot
