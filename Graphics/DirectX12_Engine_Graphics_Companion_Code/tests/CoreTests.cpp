#include "Aster/Core/FrameGraph.hpp"
#include "Aster/Core/HandlePool.hpp"
#include "Aster/Core/JobSystem.hpp"
#include "Aster/Core/LinearArena.hpp"
#include "Aster/Core/Math.hpp"
#include "Aster/Core/PbrReference.hpp"

#include <atomic>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <string_view>
#include <vector>

namespace {

int failures = 0;

void Check(bool condition, std::string_view message)
{
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

void TestMath()
{
    using namespace aster;
    const Vec3 x{1,0,0};
    const Vec3 y{0,1,0};
    const Vec3 z = Cross(x, y);
    Check(NearlyEqual(z.x, 0) && NearlyEqual(z.y, 0) && NearlyEqual(z.z, 1),
          "cross product");
    Check(NearlyEqual(Length(SafeNormalize(Vec3{3,0,0})), 1.0f),
          "safe normalize");
    const Vec3 fallback = SafeNormalize(Vec3{});
    Check(NearlyEqual(fallback.z, 1.0f), "zero normalize fallback");

    const Mat4 model = Translation({1,2,3}) * Scale({2,2,2});
    const Vec4 p = model * Vec4{1,1,1,1};
    Check(NearlyEqual(p.x, 3) && NearlyEqual(p.y, 4) && NearlyEqual(p.z, 5),
          "matrix composition");

    const Mat4 projection = PerspectiveReversedZRH(1.0f, 16.0f/9.0f, 0.1f, 1000.0f);
    const Vec4 nearClip = projection * Vec4{0,0,-0.1f,1};
    const Vec4 farClip = projection * Vec4{0,0,-1000.0f,1};
    Check(NearlyEqual(nearClip.z / nearClip.w, 1.0f, 1.0e-4f),
          "reversed-Z near maps to one");
    Check(NearlyEqual(farClip.z / farClip.w, 0.0f, 1.0e-4f),
          "reversed-Z far maps to zero");
}

struct EnemyTag {};
struct Enemy { int hp; };

void TestHandlePool()
{
    aster::HandlePool<Enemy, EnemyTag> pool;
    const auto first = pool.Create(Enemy{100});
    Check(pool.IsAlive(first), "new handle alive");
    Check(pool.Get(first).hp == 100, "handle access");
    Check(pool.Destroy(first), "destroy live handle");
    Check(!pool.IsAlive(first), "stale handle rejected");

    const auto second = pool.Create(Enemy{50});
    Check(second.index == first.index, "slot reused");
    Check(second.generation != first.generation, "generation changed");
}

void TestLinearArena()
{
    aster::LinearArena arena(1024);
    struct alignas(32) Aligned { int value; };
    Aligned* object = arena.Create<Aligned>(Aligned{42});
    Check(reinterpret_cast<std::uintptr_t>(object) % alignof(Aligned) == 0,
          "arena alignment");
    Check(object->value == 42, "arena construction");
    Check(arena.Used() >= sizeof(Aligned), "arena usage");
    arena.Reset();
    Check(arena.Used() == 0, "arena reset");
}

void TestFrameGraph()
{
    using namespace aster;
    FrameGraph graph;
    const auto depth = graph.AddResource("Depth");
    const auto gbuffer = graph.AddResource("GBuffer");
    const auto hdr = graph.AddResource("HDR");

    const std::vector<ResourceUse> depthUses{{depth, AccessMode::Write}};
    const std::vector<ResourceUse> gbufferUses{
        {depth, AccessMode::Read},
        {gbuffer, AccessMode::Write}
    };
    const std::vector<ResourceUse> lightUses{
        {depth, AccessMode::Read},
        {gbuffer, AccessMode::Read},
        {hdr, AccessMode::Write}
    };

    const auto p0 = graph.AddPass("DepthPrepass", depthUses);
    const auto p1 = graph.AddPass("GBuffer", gbufferUses);
    const auto p2 = graph.AddPass("Lighting", lightUses, true);
    const auto compiled = graph.Compile();

    Check(compiled.order.size() == 3, "frame graph order size");
    Check(compiled.order[0] == p0 && compiled.order[1] == p1 && compiled.order[2] == p2,
          "frame graph dependency order");
    Check(compiled.firstUse[depth.id] == 0 && compiled.lastUse[depth.id] == 2,
          "resource lifetime");
    Check(graph.ToDot(compiled).find("DepthPrepass") != std::string::npos,
          "dot output");
}

void TestJobSystem()
{
    aster::JobSystem jobs(3);
    constexpr std::uint32_t count = 10000;
    std::vector<std::uint32_t> output(count, 0);
    const auto handle = jobs.Dispatch(count, 127, [&](std::uint32_t i) {
        output[i] = i * 2;
    });
    jobs.Wait(handle);
    Check(handle.IsComplete(), "job complete");
    Check(output[1234] == 2468, "parallel output");

    std::atomic_uint64_t sum{};
    const auto sumHandle = jobs.Dispatch(count, 64, [&](std::uint32_t i) {
        sum.fetch_add(i, std::memory_order_relaxed);
    });
    jobs.Wait(sumHandle);
    const std::uint64_t expected = (static_cast<std::uint64_t>(count) - 1) * count / 2;
    Check(sum.load() == expected, "parallel sum");
}

void TestPbr()
{
    using namespace aster;
    MaterialSample dielectric{{0.8f, 0.2f, 0.1f}, 0.0f, 0.5f};
    const Vec3 value = EvaluatePbr(dielectric, {0,0,1}, {0,0,1}, {0,0,1});
    Check(std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z),
          "PBR finite");
    Check(value.x >= 0 && value.y >= 0 && value.z >= 0, "PBR non-negative");

    MaterialSample metal{{0.9f, 0.7f, 0.2f}, 1.0f, 0.2f};
    const Vec3 metalValue = EvaluatePbr(metal, {0,0,1}, {0,0,1}, {0,0,1});
    Check(metalValue.x > metalValue.z, "metal colored specular");
}

} // namespace

int main()
{
    TestMath();
    TestHandlePool();
    TestLinearArena();
    TestFrameGraph();
    TestJobSystem();
    TestPbr();

    if (failures == 0) {
        std::cout << "All portable companion tests passed.\n";
        return EXIT_SUCCESS;
    }
    std::cerr << failures << " test(s) failed.\n";
    return EXIT_FAILURE;
}
