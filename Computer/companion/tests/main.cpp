#include "apex/Bits.hpp"
#include "apex/Expression.hpp"
#include "apex/GameLoop.hpp"
#include "apex/Graph.hpp"
#include "apex/HandlePool.hpp"
#include "apex/LinearArena.hpp"
#include "apex/Tiny8.hpp"
#include "apex/WalKv.hpp"

#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
int failures = 0;
#define CHECK(expr) do { if (!(expr)) { std::cerr << __FILE__ << ':' << __LINE__ << " CHECK failed: " #expr "\n"; ++failures; } } while (false)
#define CHECK_NEAR(a,b,e) CHECK(std::fabs((a)-(b)) <= (e))

void test_bits() {
    auto r = apex::add8(0xFFU, 1U);
    CHECK(r.value == 0U && r.carry && !r.overflow && r.zero);
    r = apex::add8(0x7FU, 1U);
    CHECK(r.value == 0x80U && !r.carry && r.overflow && r.negative);
}

struct ThingTag {};
struct Thing { int value; };
void test_handles() {
    apex::HandlePool<Thing, ThingTag> pool;
    const auto a = pool.emplace(Thing{7});
    CHECK(pool.valid(a));
    CHECK(pool.try_get(a)->value == 7);
    CHECK(pool.destroy(a));
    CHECK(!pool.valid(a));
    const auto b = pool.emplace(Thing{9});
    CHECK(b.index == a.index);
    CHECK(b.generation != a.generation);
    CHECK(pool.try_get(a) == nullptr);
    CHECK(pool.try_get(b)->value == 9);
}

void test_arena() {
    apex::LinearArena arena(128U);
    auto* a = arena.make<std::uint32_t>(42U);
    auto* b = arena.make<double>(3.5);
    CHECK(*a == 42U);
    CHECK_NEAR(*b, 3.5, 1e-12);
    CHECK(reinterpret_cast<std::uintptr_t>(b) % alignof(double) == 0U);
    CHECK(arena.used() > 0U);
    arena.reset();
    CHECK(arena.used() == 0U);
}

void test_tiny8() {
    using namespace apex::tiny8;
    Cpu cpu;
    const std::vector<std::uint8_t> p{
        static_cast<std::uint8_t>(Op::LdaImm), 250,
        static_cast<std::uint8_t>(Op::LdbImm), 10,
        static_cast<std::uint8_t>(Op::AddB),
        static_cast<std::uint8_t>(Op::StaMem), 0xF0,
        static_cast<std::uint8_t>(Op::Halt),
    };
    load(cpu, p);
    CHECK(run(cpu) == StepStatus::Halted);
    CHECK(cpu.a == 4U);
    CHECK(cpu.carry);
    CHECK(cpu.memory[0xF0] == 4U);

    Cpu call_cpu;
    const std::vector<std::uint8_t> call_program{
        static_cast<std::uint8_t>(Op::Call), 4,
        static_cast<std::uint8_t>(Op::Halt),
        static_cast<std::uint8_t>(Op::Nop),
        static_cast<std::uint8_t>(Op::LdaImm), 33,
        static_cast<std::uint8_t>(Op::Ret),
    };
    load(call_cpu, call_program);
    CHECK(run(call_cpu) == StepStatus::Halted);
    CHECK(call_cpu.a == 33U);
    CHECK(call_cpu.sp == 0xFFU);
}

void test_expression() {
    CHECK_NEAR(apex::expr::evaluate("2 * (3 + 4) - -5"), 19.0, 1e-12);
    CHECK_NEAR(apex::expr::evaluate("10 / 4"), 2.5, 1e-12);
    bool threw = false;
    try { static_cast<void>(apex::expr::evaluate("1 / 0")); }
    catch (const std::runtime_error&) { threw = true; }
    CHECK(threw);
}

void test_graph() {
    const std::vector<std::vector<std::size_t>> dag{{1,2},{3},{3},{}};
    const auto sorted = apex::topological_sort(dag);
    CHECK(sorted.cycle_nodes.empty());
    CHECK(sorted.order.size() == 4U);
    std::vector<std::size_t> pos(4U);
    for (std::size_t i=0;i<sorted.order.size();++i) pos[sorted.order[i]]=i;
    CHECK(pos[0] < pos[1] && pos[0] < pos[2] && pos[1] < pos[3] && pos[2] < pos[3]);

    const std::vector<std::vector<std::size_t>> cycle{{1},{2},{0}};
    const auto bad = apex::topological_sort(cycle);
    CHECK(!bad.cycle_nodes.empty());
}

void test_stepper() {
    apex::FixedStepper stepper(0.01, 4U);
    int updates = 0;
    const auto n = stepper.advance(0.035, [&](double dt) { CHECK_NEAR(dt, 0.01, 1e-12); ++updates; });
    CHECK(n == 3U && updates == 3 && stepper.tick() == 3U);
    CHECK_NEAR(stepper.alpha(), 0.5, 1e-12);
}

std::filesystem::path temp_file(const char* name) {
    auto p = std::filesystem::temp_directory_path() / name;
    std::error_code ec;
    std::filesystem::remove(p, ec);
    return p;
}

void test_wal_kv() {
    const auto path = temp_file("apex_stonekv_test.wal");
    {
        apex::WalKv kv(path);
        kv.open_or_recover();
        kv.put("player", "alice");
        kv.put("score", "42");
        kv.erase("player");
        CHECK(!kv.get("player"));
        CHECK(kv.get("score") == std::optional<std::string>{"42"});
    }
    {
        apex::WalKv kv(path);
        kv.open_or_recover();
        CHECK(kv.size() == 1U);
        CHECK(kv.get("score") == std::optional<std::string>{"42"});
    }
    // A partial final record must not invalidate the committed prefix.
    {
        std::ofstream out(path, std::ios::binary | std::ios::app);
        const char partial[] = {'S','K','V'};
        out.write(partial, 3);
    }
    {
        apex::WalKv kv(path);
        kv.open_or_recover();
        CHECK(kv.get("score") == std::optional<std::string>{"42"});
    }
    std::error_code ec;
    std::filesystem::remove(path, ec);
}
} // namespace

int main() {
    test_bits();
    test_handles();
    test_arena();
    test_tiny8();
    test_expression();
    test_graph();
    test_stepper();
    test_wal_kv();
    if (failures != 0) {
        std::cerr << failures << " test assertion(s) failed\n";
        return 1;
    }
    std::cout << "All Apex Foundations tests passed.\n";
    return 0;
}
