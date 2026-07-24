#include "apex/Graph.hpp"

#include <queue>
#include <stdexcept>

namespace apex {

TopologyResult topological_sort(const std::vector<std::vector<std::size_t>>& outgoing) {
    std::vector<std::size_t> indegree(outgoing.size(), 0U);
    for (std::size_t from = 0; from < outgoing.size(); ++from) {
        for (const auto to : outgoing[from]) {
            if (to >= outgoing.size()) throw std::out_of_range("graph edge target out of range");
            ++indegree[to];
        }
    }
    std::priority_queue<std::size_t, std::vector<std::size_t>, std::greater<>> ready;
    for (std::size_t i = 0; i < indegree.size(); ++i) if (indegree[i] == 0U) ready.push(i);

    TopologyResult result;
    while (!ready.empty()) {
        const auto node = ready.top();
        ready.pop();
        result.order.push_back(node);
        for (const auto to : outgoing[node]) {
            if (--indegree[to] == 0U) ready.push(to);
        }
    }
    if (result.order.size() != outgoing.size()) {
        for (std::size_t i = 0; i < indegree.size(); ++i) if (indegree[i] != 0U) result.cycle_nodes.push_back(i);
    }
    return result;
}

} // namespace apex
