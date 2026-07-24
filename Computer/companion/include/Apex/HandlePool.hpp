#pragma once

#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <utility>
#include <vector>

namespace apex {

template<class Tag>
struct Handle {
    std::uint32_t index{std::numeric_limits<std::uint32_t>::max()};
    std::uint32_t generation{};

    friend constexpr bool operator==(Handle, Handle) = default;
    [[nodiscard]] constexpr explicit operator bool() const noexcept {
        return index != std::numeric_limits<std::uint32_t>::max();
    }
};

template<class T, class Tag = T>
class HandlePool {
public:
    using handle_type = Handle<Tag>;

    template<class... Args>
    handle_type emplace(Args&&... args) {
        std::uint32_t index{};
        if (!free_.empty()) {
            index = free_.back();
            free_.pop_back();
            auto& slot = slots_.at(index);
            slot.value.emplace(std::forward<Args>(args)...);
            slot.alive = true;
        } else {
            if (slots_.size() >= std::numeric_limits<std::uint32_t>::max()) {
                throw std::length_error("HandlePool index space exhausted");
            }
            index = static_cast<std::uint32_t>(slots_.size());
            Slot slot;
            slot.value.emplace(std::forward<Args>(args)...);
            slot.alive = true;
            slots_.push_back(std::move(slot));
        }
        return handle_type{index, slots_[index].generation};
    }

    bool destroy(handle_type handle) noexcept {
        if (!valid(handle)) return false;
        auto& slot = slots_[handle.index];
        slot.value.reset();
        slot.alive = false;
        ++slot.generation;
        free_.push_back(handle.index);
        return true;
    }

    [[nodiscard]] T* try_get(handle_type handle) noexcept {
        if (!valid(handle)) return nullptr;
        return std::addressof(*slots_[handle.index].value);
    }

    [[nodiscard]] const T* try_get(handle_type handle) const noexcept {
        if (!valid(handle)) return nullptr;
        return std::addressof(*slots_[handle.index].value);
    }

    [[nodiscard]] bool valid(handle_type handle) const noexcept {
        return handle.index < slots_.size() &&
               slots_[handle.index].alive &&
               slots_[handle.index].generation == handle.generation;
    }

    [[nodiscard]] std::size_t capacity_slots() const noexcept { return slots_.size(); }
    [[nodiscard]] std::size_t live_count() const noexcept { return slots_.size() - free_.size(); }

private:
    struct Slot {
        std::optional<T> value;
        std::uint32_t generation{1};
        bool alive{false};
    };

    std::vector<Slot> slots_;
    std::vector<std::uint32_t> free_;
};

} // namespace apex
