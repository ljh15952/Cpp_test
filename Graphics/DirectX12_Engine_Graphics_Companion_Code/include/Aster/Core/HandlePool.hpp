#pragma once

#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <utility>
#include <vector>

namespace aster {

template<class Tag>
struct Handle {
    std::uint32_t index{std::numeric_limits<std::uint32_t>::max()};
    std::uint32_t generation{};
    friend bool operator==(Handle, Handle) = default;
};

template<class T, class Tag>
class HandlePool {
public:
    using HandleType = Handle<Tag>;

    template<class... Args>
    HandleType Create(Args&&... args) {
        std::uint32_t index{};
        if (!free_.empty()) {
            index = free_.back();
            free_.pop_back();
            slots_[index].value.emplace(std::forward<Args>(args)...);
            slots_[index].alive = true;
        } else {
            index = static_cast<std::uint32_t>(slots_.size());
            slots_.push_back(Slot{
                .value = std::optional<T>{std::in_place, std::forward<Args>(args)...},
                .generation = 1,
                .alive = true
            });
        }
        return {index, slots_[index].generation};
    }

    bool Destroy(HandleType handle) {
        if (!IsAlive(handle)) return false;
        Slot& slot = slots_[handle.index];
        slot.value.reset();
        slot.alive = false;
        ++slot.generation;
        if (slot.generation == 0) ++slot.generation;
        free_.push_back(handle.index);
        return true;
    }

    [[nodiscard]] bool IsAlive(HandleType handle) const noexcept {
        return handle.index < slots_.size()
            && slots_[handle.index].alive
            && slots_[handle.index].generation == handle.generation;
    }

    [[nodiscard]] T* TryGet(HandleType handle) noexcept {
        return IsAlive(handle) ? &*slots_[handle.index].value : nullptr;
    }

    [[nodiscard]] const T* TryGet(HandleType handle) const noexcept {
        return IsAlive(handle) ? &*slots_[handle.index].value : nullptr;
    }

    T& Get(HandleType handle) {
        if (T* value = TryGet(handle)) return *value;
        throw std::out_of_range("stale or invalid handle");
    }

    [[nodiscard]] std::size_t Capacity() const noexcept { return slots_.size(); }

private:
    struct Slot {
        std::optional<T> value;
        std::uint32_t generation{1};
        bool alive{};
    };

    std::vector<Slot> slots_;
    std::vector<std::uint32_t> free_;
};

} // namespace aster
