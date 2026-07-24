#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <new>
#include <span>
#include <stdexcept>
#include <type_traits>
#include <utility>
#include <vector>

namespace apex {

class LinearArena {
public:
    explicit LinearArena(std::size_t capacity) : storage_(capacity) {}

    [[nodiscard]] void* allocate(std::size_t bytes, std::size_t alignment) {
        if (alignment == 0U || (alignment & (alignment - 1U)) != 0U) {
            throw std::invalid_argument("alignment must be a non-zero power of two");
        }
        const std::size_t aligned = (offset_ + alignment - 1U) & ~(alignment - 1U);
        if (aligned > storage_.size() || bytes > storage_.size() - aligned) {
            throw std::bad_alloc{};
        }
        void* result = storage_.data() + aligned;
        offset_ = aligned + bytes;
        peak_ = offset_ > peak_ ? offset_ : peak_;
        return result;
    }

    template<class T, class... Args>
    T* make(Args&&... args) {
        static_assert(std::is_trivially_destructible_v<T>,
                      "This teaching arena resets without running destructors");
        void* memory = allocate(sizeof(T), alignof(T));
        return std::construct_at(static_cast<T*>(memory), std::forward<Args>(args)...);
    }

    void reset() noexcept { offset_ = 0U; }
    [[nodiscard]] std::size_t used() const noexcept { return offset_; }
    [[nodiscard]] std::size_t peak() const noexcept { return peak_; }
    [[nodiscard]] std::size_t capacity() const noexcept { return storage_.size(); }

private:
    std::vector<std::byte> storage_;
    std::size_t offset_{};
    std::size_t peak_{};
};

} // namespace apex
