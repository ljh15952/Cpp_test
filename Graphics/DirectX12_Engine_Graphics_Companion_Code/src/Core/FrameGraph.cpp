#include "Aster/Core/FrameGraph.hpp"

#include <algorithm>
#include <limits>
#include <queue>
#include <sstream>
#include <unordered_set>

namespace aster {

ResourceHandle FrameGraph::AddResource(std::string name)
{
    const auto id = static_cast<std::uint32_t>(resources_.size());
    resources_.push_back(Resource{std::move(name)});
    return {id};
}

PassHandle FrameGraph::AddPass(std::string name,
                               std::span<const ResourceUse> uses,
                               bool sideEffect)
{
    for (const ResourceUse& use : uses) {
        if (use.resource.id >= resources_.size()) {
            throw std::out_of_range("frame graph pass references invalid resource");
        }
    }
    const auto id = static_cast<std::uint32_t>(passes_.size());
    passes_.push_back(Pass{std::move(name), {uses.begin(), uses.end()}, sideEffect});
    return {id};
}

CompiledFrameGraph FrameGraph::Compile() const
{
    const std::size_t passCount = passes_.size();
    const std::size_t resourceCount = resources_.size();

    std::vector<std::unordered_set<std::uint32_t>> edgeSets(passCount);

    struct ResourceState {
        std::optional<std::uint32_t> lastWriter;
        std::vector<std::uint32_t> readers;
    };
    std::vector<ResourceState> state(resourceCount);

    auto addEdge = [&](std::uint32_t from, std::uint32_t to) {
        if (from != to) edgeSets[from].insert(to);
    };

    for (std::uint32_t passId = 0; passId < passCount; ++passId) {
        // Normalize duplicate uses in one pass to the strongest access.
        std::unordered_map<std::uint32_t, AccessMode> normalized;
        for (const ResourceUse& use : passes_[passId].uses) {
            auto [it, inserted] = normalized.emplace(use.resource.id, use.access);
            if (!inserted && it->second != use.access) {
                it->second = AccessMode::ReadWrite;
            }
        }

        for (const auto& [resourceId, access] : normalized) {
            ResourceState& s = state[resourceId];
            const bool reads = access == AccessMode::Read || access == AccessMode::ReadWrite;
            const bool writes = access == AccessMode::Write || access == AccessMode::ReadWrite;

            if (reads && s.lastWriter) addEdge(*s.lastWriter, passId);

            if (writes) {
                if (s.lastWriter) addEdge(*s.lastWriter, passId);
                for (std::uint32_t reader : s.readers) addEdge(reader, passId);
                s.readers.clear();
                s.lastWriter = passId;
            } else if (reads) {
                s.readers.push_back(passId);
            }
        }
    }

    CompiledFrameGraph out;
    out.outgoing.resize(passCount);
    std::vector<std::uint32_t> indegree(passCount, 0);
    for (std::uint32_t from = 0; from < passCount; ++from) {
        out.outgoing[from].reserve(edgeSets[from].size());
        for (std::uint32_t to : edgeSets[from]) {
            out.outgoing[from].push_back(PassHandle{to});
            ++indegree[to];
        }
        std::sort(out.outgoing[from].begin(), out.outgoing[from].end(),
                  [](PassHandle a, PassHandle b) { return a.id < b.id; });
    }

    std::priority_queue<std::uint32_t,
                        std::vector<std::uint32_t>,
                        std::greater<>> ready;
    for (std::uint32_t i = 0; i < passCount; ++i) {
        if (indegree[i] == 0) ready.push(i);
    }

    while (!ready.empty()) {
        const std::uint32_t p = ready.top();
        ready.pop();
        out.order.push_back(PassHandle{p});
        for (PassHandle next : out.outgoing[p]) {
            if (--indegree[next.id] == 0) ready.push(next.id);
        }
    }

    if (out.order.size() != passCount) {
        std::ostringstream message;
        message << "frame graph contains a cycle involving:";
        for (std::uint32_t i = 0; i < passCount; ++i) {
            if (indegree[i] != 0) message << ' ' << passes_[i].name;
        }
        throw std::logic_error(message.str());
    }

    const std::uint32_t never = std::numeric_limits<std::uint32_t>::max();
    out.firstUse.assign(resourceCount, never);
    out.lastUse.assign(resourceCount, 0);

    for (std::uint32_t orderIndex = 0; orderIndex < out.order.size(); ++orderIndex) {
        const Pass& pass = passes_[out.order[orderIndex].id];
        for (const ResourceUse& use : pass.uses) {
            auto& first = out.firstUse[use.resource.id];
            first = std::min(first, orderIndex);
            out.lastUse[use.resource.id] = std::max(out.lastUse[use.resource.id], orderIndex);
        }
    }
    return out;
}

std::string FrameGraph::ToDot(const CompiledFrameGraph& compiled) const
{
    std::ostringstream out;
    out << "digraph FrameGraph {\n  rankdir=LR;\n";
    for (std::uint32_t i = 0; i < passes_.size(); ++i) {
        out << "  p" << i << " [label=\"" << passes_[i].name << "\"];\n";
    }
    for (std::uint32_t from = 0; from < compiled.outgoing.size(); ++from) {
        for (PassHandle to : compiled.outgoing[from]) {
            out << "  p" << from << " -> p" << to.id << ";\n";
        }
    }
    out << "}\n";
    return out.str();
}

std::string_view FrameGraph::ResourceName(ResourceHandle h) const
{
    if (h.id >= resources_.size()) throw std::out_of_range("invalid resource handle");
    return resources_[h.id].name;
}

std::string_view FrameGraph::PassName(PassHandle h) const
{
    if (h.id >= passes_.size()) throw std::out_of_range("invalid pass handle");
    return passes_[h.id].name;
}

} // namespace aster
