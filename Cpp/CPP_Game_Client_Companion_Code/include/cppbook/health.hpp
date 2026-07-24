#pragma once

#include <algorithm>
#include <stdexcept>

namespace cppbook {

class Health final {
public:
    explicit Health(int maximum)
        : current_(maximum), maximum_(maximum) {
        if (maximum <= 0) {
            throw std::invalid_argument("maximum health must be positive");
        }
    }

    [[nodiscard]] int current() const noexcept { return current_; }
    [[nodiscard]] int maximum() const noexcept { return maximum_; }
    [[nodiscard]] bool is_dead() const noexcept { return current_ == 0; }

    int damage(int amount) {
        require_non_negative(amount);
        const int applied = std::min(current_, amount);
        current_ -= applied;
        return applied;
    }

    int heal(int amount) {
        require_non_negative(amount);
        const int applied = std::min(maximum_ - current_, amount);
        current_ += applied;
        return applied;
    }

    void kill() noexcept { current_ = 0; }

private:
    static void require_non_negative(int amount) {
        if (amount < 0) {
            throw std::invalid_argument("amount must be non-negative");
        }
    }

    int current_;
    int maximum_;
};

} // namespace cppbook
