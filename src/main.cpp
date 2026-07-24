#include "cppbook/fixed_stepper.hpp"
#include "cppbook/handle_pool.hpp"
#include "cppbook/health.hpp"
#include "cppbook/math.hpp"
#include "cppbook/state_machine.hpp"
#include "cppbook/statistics.hpp"

#include <array>
#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

struct Enemy final {
    std::string name;
    int health{};

    Enemy(std::string enemy_name, int enemy_health)
        : name(std::move(enemy_name)), health(enemy_health) {}
};

void test_health() {
    cppbook::Health health{100};
    assert(health.damage(30) == 30);
    assert(health.current() == 70);
    assert(health.heal(50) == 30);
    assert(health.current() == 100);
    assert(health.damage(500) == 100);
    assert(health.is_dead());

    bool threw = false;
    try {
        static_cast<void>(health.damage(-1));
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    assert(threw);
}

void test_handle_pool() {
    cppbook::HandlePool<Enemy> enemies;
    const cppbook::Handle first = enemies.create("Slime", 10);
    assert(enemies.alive() == 1U);
    assert(enemies.get(first) != nullptr);
    assert(enemies.get(first)->name == "Slime");

    assert(enemies.destroy(first));
    assert(enemies.get(first) == nullptr); // Stale generation is rejected.

    const cppbook::Handle second = enemies.create("Orc", 50);
    assert(second.index == first.index);       // Slot was reused.
    assert(second.generation != first.generation);
    assert(enemies.get(second)->health == 50);
}

void test_fixed_stepper() {
    cppbook::FixedStepper stepper{1.0 / 60.0, 0.25, 8};
    int updates = 0;
    double simulated_seconds = 0.0;

    const int first_steps = stepper.advance(1.0 / 30.0, [&](double dt) {
        ++updates;
        simulated_seconds += dt;
    });

    assert(first_steps == 2);
    assert(updates == 2);
    assert(std::abs(simulated_seconds - (2.0 / 60.0)) < 1.0e-9);
    assert(stepper.alpha() >= 0.0 && stepper.alpha() < 1.0);
}

void test_state_machine() {
    using cppbook::PlayerEvent;
    using cppbook::PlayerState;

    cppbook::PlayerStateMachine machine;
    assert(machine.state() == PlayerState::idle);

    auto result = machine.handle(PlayerEvent::move_started);
    assert(result.transitioned && machine.state() == PlayerState::run);

    result = machine.handle(PlayerEvent::dodge_pressed);
    assert(result.transitioned && machine.state() == PlayerState::dodge);

    result = machine.handle(PlayerEvent::normal_hit);
    assert(result.event_consumed && !result.transitioned);
    assert(machine.state() == PlayerState::dodge);

    result = machine.handle(PlayerEvent::unblockable_hit);
    assert(result.transitioned && machine.state() == PlayerState::stun);

    result = machine.handle(PlayerEvent::health_depleted);
    assert(result.transitioned && machine.state() == PlayerState::dead);

    result = machine.handle(PlayerEvent::animation_finished);
    assert(!result.event_consumed && !result.transitioned);
    assert(machine.state() == PlayerState::dead);
}

void test_math() {
    const cppbook::Vec3 x{1.0F, 0.0F, 0.0F};
    const cppbook::Vec3 y{0.0F, 1.0F, 0.0F};
    const cppbook::Vec3 z = cppbook::cross(x, y);
    assert(cppbook::nearly_equal(z.x, 0.0F));
    assert(cppbook::nearly_equal(z.y, 0.0F));
    assert(cppbook::nearly_equal(z.z, 1.0F));
    assert(cppbook::nearly_equal(cppbook::dot(x, y), 0.0F));

    const auto normalized = cppbook::normalize(cppbook::Vec3{3.0F, 0.0F, 4.0F});
    assert(normalized.has_value());
    assert(cppbook::nearly_equal(cppbook::length_squared(*normalized), 1.0F));
    assert(!cppbook::normalize(cppbook::Vec3{}).has_value());
}

void test_statistics() {
    constexpr std::array<double, 5> samples{1.0, 2.0, 3.0, 4.0, 100.0};
    assert(std::abs(cppbook::mean(samples) - 22.0) < 1.0e-9);
    assert(std::abs(cppbook::percentile(samples, 0.5) - 3.0) < 1.0e-9);
    assert(std::abs(cppbook::percentile(samples, 0.95) - 80.8) < 1.0e-9);
}

} // namespace

int main() {
    test_health();
    test_handle_pool();
    test_fixed_stepper();
    test_state_machine();
    test_math();
    test_statistics();

    std::cout << "All companion-code self-tests passed.\n";
}
