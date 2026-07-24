#pragma once

#include <string_view>

namespace cppbook {

enum class PlayerState {
    idle,
    run,
    attack,
    dodge,
    stun,
    dead,
};

enum class PlayerEvent {
    move_started,
    move_stopped,
    attack_pressed,
    dodge_pressed,
    normal_hit,
    unblockable_hit,
    animation_finished,
    health_depleted,
};

struct TransitionResult final {
    PlayerState previous{};
    PlayerState current{};
    bool event_consumed{};
    bool transitioned{};
};

class PlayerStateMachine final {
public:
    [[nodiscard]] PlayerState state() const noexcept { return state_; }

    [[nodiscard]] TransitionResult handle(PlayerEvent event) noexcept {
        const PlayerState previous = state_;

        // Dead is terminal. All later events are deliberately rejected.
        if (state_ == PlayerState::dead) {
            return {previous, state_, false, false};
        }

        // Global transition with the highest priority.
        if (event == PlayerEvent::health_depleted) {
            state_ = PlayerState::dead;
            return {previous, state_, true, previous != state_};
        }

        // Dodge ignores ordinary hits, but not explicitly unblockable hits.
        if (event == PlayerEvent::normal_hit) {
            if (state_ == PlayerState::dodge) {
                return {previous, state_, true, false};
            }
            state_ = PlayerState::stun;
            return {previous, state_, true, previous != state_};
        }

        if (event == PlayerEvent::unblockable_hit) {
            state_ = PlayerState::stun;
            return {previous, state_, true, previous != state_};
        }

        switch (state_) {
        case PlayerState::idle:
            if (event == PlayerEvent::move_started) {
                state_ = PlayerState::run;
            } else if (event == PlayerEvent::attack_pressed) {
                state_ = PlayerState::attack;
            } else if (event == PlayerEvent::dodge_pressed) {
                state_ = PlayerState::dodge;
            } else {
                return {previous, state_, false, false};
            }
            break;

        case PlayerState::run:
            if (event == PlayerEvent::move_stopped) {
                state_ = PlayerState::idle;
            } else if (event == PlayerEvent::attack_pressed) {
                state_ = PlayerState::attack;
            } else if (event == PlayerEvent::dodge_pressed) {
                state_ = PlayerState::dodge;
            } else {
                return {previous, state_, false, false};
            }
            break;

        case PlayerState::attack:
        case PlayerState::dodge:
        case PlayerState::stun:
            if (event == PlayerEvent::animation_finished) {
                state_ = PlayerState::idle;
            } else {
                return {previous, state_, false, false};
            }
            break;

        case PlayerState::dead:
            // Handled above. This case keeps the switch exhaustive.
            return {previous, state_, false, false};
        }

        return {previous, state_, true, previous != state_};
    }

private:
    PlayerState state_{PlayerState::idle};
};

[[nodiscard]] constexpr std::string_view to_string(PlayerState state) noexcept {
    switch (state) {
    case PlayerState::idle: return "Idle";
    case PlayerState::run: return "Run";
    case PlayerState::attack: return "Attack";
    case PlayerState::dodge: return "Dodge";
    case PlayerState::stun: return "Stun";
    case PlayerState::dead: return "Dead";
    }
    return "Unknown";
}

} // namespace cppbook
