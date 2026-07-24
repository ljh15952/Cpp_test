#include "apex/Bits.hpp"
#include "apex/Expression.hpp"
#include "apex/GameLoop.hpp"
#include "apex/HandlePool.hpp"
#include "apex/Tiny8.hpp"

#include <cstdint>
#include <iostream>
#include <vector>

struct EntityTag {};
struct Entity { int health; };

int main() {
    const auto sum = apex::add8(0x7FU, 1U);
    std::cout << "0x7F + 1 = " << static_cast<int>(sum.value)
              << ", signed-overflow=" << sum.overflow << '\n';

    std::cout << "Mori expression: 2 * (3 + 4) - 5 = "
              << apex::expr::evaluate("2 * (3 + 4) - 5") << '\n';

    apex::HandlePool<Entity, EntityTag> entities;
    const auto player = entities.emplace(Entity{100});
    std::cout << "entity health=" << entities.try_get(player)->health << '\n';
    entities.destroy(player);
    std::cout << "stale handle valid=" << entities.valid(player) << '\n';

    using namespace apex::tiny8;
    Cpu cpu;
    const std::vector<std::uint8_t> program{
        static_cast<std::uint8_t>(Op::LdaImm), 7,
        static_cast<std::uint8_t>(Op::LdbImm), 5,
        static_cast<std::uint8_t>(Op::AddB),
        static_cast<std::uint8_t>(Op::Halt),
    };
    load(cpu, program);
    const auto status = run(cpu);
    std::cout << "Tiny8 status=" << static_cast<int>(status) << ", A=" << static_cast<int>(cpu.a) << '\n';

    apex::FixedStepper stepper(1.0 / 60.0, 5);
    double position = 0.0;
    stepper.advance(1.0 / 30.0, [&](double dt) { position += 3.0 * dt; });
    std::cout << "fixed ticks=" << stepper.tick() << ", position=" << position << '\n';
}
