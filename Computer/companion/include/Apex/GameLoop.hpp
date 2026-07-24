#pragma once

#include <algorithm>
#include <cstddef>
#include <cmath>
#include <functional>
#include <stdexcept>

namespace apex {

class FixedStepper {
public:
    FixedStepper(double step_seconds, std::size_t max_steps_per_frame)
        : step_(step_seconds), max_steps_(max_steps_per_frame) {
        if (!(step_ > 0.0) || max_steps_ == 0U) throw std::invalid_argument("invalid fixed step configuration");
    }

    template<class Simulate>
    std::size_t advance(double frame_seconds, Simulate&& simulate) {
        frame_seconds = std::clamp(frame_seconds, 0.0, step_ * static_cast<double>(max_steps_) * 2.0);
        accumulator_ += frame_seconds;
        std::size_t steps = 0;
        while (accumulator_ >= step_ && steps < max_steps_) {
            std::invoke(simulate, step_);
            accumulator_ -= step_;
            ++steps;
            ++tick_;
        }
        if (steps == max_steps_ && accumulator_ >= step_) {
            dropped_time_ += accumulator_ - std::fmod(accumulator_, step_);
            accumulator_ = std::fmod(accumulator_, step_);
        }
        return steps;
    }

    [[nodiscard]] double alpha() const noexcept { return accumulator_ / step_; }
    [[nodiscard]] std::size_t tick() const noexcept { return tick_; }
    [[nodiscard]] double dropped_time() const noexcept { return dropped_time_; }

private:
    double step_{};
    std::size_t max_steps_{};
    double accumulator_{};
    std::size_t tick_{};
    double dropped_time_{};
};

} // namespace apex
