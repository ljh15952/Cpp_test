#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <new>
#include <span>
#include <stdexcept>
#include <type_traits>
#include <utility>
#include <vector>

namespace aster {

class LinearArena {
public:
    explicit LinearArena(std::size_t bytes) : storage_(bytes) {}

    void Reset() noexcept { offset_ = 0; }

    [[nodiscard]] std::size_t Used() const noexcept { return offset_; }
    [[nodiscard]] std::size_t Capacity() const noexcept { return storage_.size(); }

    void* AllocateBytes(std::size_t bytes,
                        std::size_t alignment = alignof(std::max_align_t)) {
        void* current = storage_.data() + offset_;
        std::size_t space = storage_.size() - offset_;
        void* aligned = std::align(alignment, bytes, current, space);
        if (!aligned) throw std::bad_alloc{};
        const auto alignedOffset = static_cast<std::byte*>(aligned) - storage_.data();
        offset_ = static_cast<std::size_t>(alignedOffset) + bytes;
        return aligned;
    }

    template<class T, class... Args>
    T* Create(Args&&... args) {
        void* memory = AllocateBytes(sizeof(T), alignof(T));
        return std::construct_at(static_cast<T*>(memory), std::forward<Args>(args)...);
    }

    template<class T>
    std::span<T> AllocateArray(std::size_t count) {
        static_assert(std::is_trivially_destructible_v<T>,
                      "Arena arrays are reset without destructors");
        auto* pointer = static_cast<T*>(AllocateBytes(sizeof(T) * count, alignof(T)));
        return {pointer, count};
    }

private:
    std::vector<std::byte> storage_;
    std::size_t offset_{};
};

} // namespace aster
