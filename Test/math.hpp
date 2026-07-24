#pragma once

#include <algorithm>
#include <functional>
#include <stdexcept>

namespace cppbook {

class FixedStepper final {
public:
    FixedStepper(double step_seconds = 1.0 / 60.0,
                 double max_frame_seconds = 0.25,
                 int max_steps = 8)
        : step_(step_seconds),
          max_frame_(max_frame_seconds),
          max_steps_(max_steps) {
        if (step_ <= 0.0 || max_frame_ <= 0.0 || max_steps_ <= 0) {
            throw std::invalid_argument("invalid fixed-step configuration");
        }
    }

    template <typename Update>
    int advance(double frame_seconds, Update&& update) {
        frame_seconds = std::clamp(frame_seconds, 0.0, max_frame_);
        accumulator_ += frame_seconds;

        int steps = 0;
        while (accumulator_ >= step_ && steps < max_steps_) {
            std::invoke(std::forward<Update>(update), step_);
            accumulator_ -= step_;
            ++steps;
        }

        if (steps == max_steps_ && accumulator_ >= step_) {
            accumulator_ = 0.0; // Explicit policy: drop accumulated backlog.
            dropped_backlog_ = true;
        }
        return steps;
    }

    [[nodiscard]] double alpha() const noexcept {
        return accumulator_ / step_;
    }

    [[nodiscard]] bool dropped_backlog() const noexcept {
        return dropped_backlog_;
    }

    void clear_drop_flag() noexcept { dropped_backlog_ = false; }

private:
    double step_;
    double max_frame_;
    int max_steps_;
    double accumulator_{};
    bool dropped_backlog_{};
};

} // namespace cppbook
