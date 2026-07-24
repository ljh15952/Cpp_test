#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <utility>
#include <vector>

namespace cppbook {

struct Handle final {
    std::uint32_t index{};
    std::uint32_t generation{};
    friend bool operator==(const Handle&, const Handle&) = default;
};

template <typename T>
class HandlePool final {
public:
    template <typename... Args>
    [[nodiscard]] Handle create(Args&&... args) {
        std::uint32_t index{};
        if (!free_indices_.empty()) {
            index = free_indices_.back();
            free_indices_.pop_back();
        } else {
            if (slots_.size() >= max_index_count()) {
                throw std::length_error("handle pool index overflow");
            }
            index = static_cast<std::uint32_t>(slots_.size());
            slots_.push_back(Slot{});
        }

        Slot& slot = slots_[index];
        if (slot.value.has_value()) {
            throw std::logic_error("attempted to create into an occupied slot");
        }
        slot.value.emplace(std::forward<Args>(args)...);
        ++alive_;
        return Handle{index, slot.generation};
    }

    [[nodiscard]] T* get(Handle handle) noexcept {
        Slot* slot = valid_slot(handle);
        return slot ? &*slot->value : nullptr;
    }

    [[nodiscard]] const T* get(Handle handle) const noexcept {
        const Slot* slot = valid_slot(handle);
        return slot ? &*slot->value : nullptr;
    }

    bool destroy(Handle handle) noexcept {
        Slot* slot = valid_slot(handle);
        if (!slot) {
            return false;
        }
        slot->value.reset();
        ++slot->generation;
        free_indices_.push_back(handle.index);
        --alive_;
        return true;
    }

    [[nodiscard]] std::size_t alive() const noexcept { return alive_; }

private:
    struct Slot final {
        std::optional<T> value;
        std::uint32_t generation{};
    };

    static constexpr std::size_t max_index_count() noexcept {
        return static_cast<std::size_t>(
            std::numeric_limits<std::uint32_t>::max());
    }

    [[nodiscard]] Slot* valid_slot(Handle handle) noexcept {
        if (handle.index >= slots_.size()) {
            return nullptr;
        }
        Slot& slot = slots_[handle.index];
        if (!slot.value || slot.generation != handle.generation) {
            return nullptr;
        }
        return &slot;
    }

    [[nodiscard]] const Slot* valid_slot(Handle handle) const noexcept {
        if (handle.index >= slots_.size()) {
            return nullptr;
        }
        const Slot& slot = slots_[handle.index];
        if (!slot.value || slot.generation != handle.generation) {
            return nullptr;
        }
        return &slot;
    }

    std::vector<Slot> slots_;
    std::vector<std::uint32_t> free_indices_;
    std::size_t alive_{};
};

} // namespace cppbook
