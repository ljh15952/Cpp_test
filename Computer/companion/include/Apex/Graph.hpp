#pragma once

#include <cstddef>
#include <optional>
#include <vector>

namespace apex {

struct TopologyResult {
    std::vector<std::size_t> order;
    std::vector<std::size_t> cycle_nodes;
};

[[nodiscard]] TopologyResult topological_sort(
    const std::vector<std::vector<std::size_t>>& outgoing);

} // namespace apex
