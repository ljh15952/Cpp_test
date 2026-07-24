#pragma once

#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace aster {

struct ResourceHandle {
    std::uint32_t id{};
    friend bool operator==(ResourceHandle, ResourceHandle) = default;
};

struct PassHandle {
    std::uint32_t id{};
    friend bool operator==(PassHandle, PassHandle) = default;
};

enum class AccessMode : std::uint8_t {
    Read,
    Write,
    ReadWrite
};

struct ResourceUse {
    ResourceHandle resource;
    AccessMode access;
};

struct CompiledFrameGraph {
    std::vector<PassHandle> order;
    std::vector<std::vector<PassHandle>> outgoing;
    std::vector<std::uint32_t> firstUse;
    std::vector<std::uint32_t> lastUse;
};

class FrameGraph {
public:
    ResourceHandle AddResource(std::string name);
    PassHandle AddPass(std::string name,
                       std::span<const ResourceUse> uses,
                       bool sideEffect = false);

    [[nodiscard]] CompiledFrameGraph Compile() const;
    [[nodiscard]] std::string ToDot(const CompiledFrameGraph& compiled) const;

    [[nodiscard]] std::string_view ResourceName(ResourceHandle h) const;
    [[nodiscard]] std::string_view PassName(PassHandle h) const;

private:
    struct Resource {
        std::string name;
    };
    struct Pass {
        std::string name;
        std::vector<ResourceUse> uses;
        bool sideEffect{};
    };

    std::vector<Resource> resources_;
    std::vector<Pass> passes_;
};

} // namespace aster
