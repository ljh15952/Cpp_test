# 119. 선택 해설

이 장은 모든 문제의 정답집이 아니다. 스스로 구현한 뒤 설계와 실패 모드를 비교하는 용도다.

## 119.1 문제 2: Safe Normalize

```cpp
struct Vec3 { float x, y, z; };

float Dot(Vec3 a, Vec3 b)
{
    return a.x*b.x + a.y*b.y + a.z*b.z;
}

Vec3 SafeNormalize(Vec3 v, Vec3 fallback = {0,0,1})
{
    const float lenSq = Dot(v, v);
    if (!(lenSq > 1e-12f) || !std::isfinite(lenSq)) {
        return fallback;
    }
    const float invLen = 1.0f / std::sqrt(lenSq);
    return {v.x*invLen, v.y*invLen, v.z*invLen};
}
```

`lenSq <= epsilon`뿐 아니라 NaN을 처리한다. `NaN > epsilon`은 false이므로 위 조건이 fallback으로 간다.

## 119.2 문제 12: Reversed-Z

부동소수점은 0 근처에 더 촘촘하다. perspective projection 뒤 depth의 비선형 분포와 floating-point 분포를 reversed-Z로 정렬하면 먼 거리 precision이 개선된다 [@upchurch2012]. 구현 조건:

- near→1, far→0 projection
- depth clear 0
- comparison `GREATER`/`GREATER_EQUAL`
- Hi-Z reduction과 shadow/depth reconstruction convention 확인

infinite far projection도 검토한다.

## 119.3 문제 24: Allocator reset

```text
CPU frame N: allocator A로 command memory 기록
CPU submits A-backed command list
GPU has not executed it yet
CPU reset A → backing memory 재사용/덮음
GPU executes corrupted command stream
```

해결은 allocator마다 마지막 제출 fence를 기록하고 완료 후 reset하는 것이다.

```cpp
void FrameCommandPool::Reset(ID3D12Fence* fence)
{
    if (fence->GetCompletedValue() < lastFence_) {
        WaitForFence(lastFence_);
    }
    DX_CHECK(allocator_->Reset());
}
```

## 119.4 문제 29: Upload ring

```cpp
struct UploadAllocation {
    std::byte* cpu;
    D3D12_GPU_VIRTUAL_ADDRESS gpu;
    uint64_t offset;
    uint64_t size;
};

UploadAllocation UploadRing::Allocate(uint64_t bytes, uint64_t alignment)
{
    uint64_t begin = AlignUp(head_, alignment);
    if (begin + bytes > capacity_) {
        throw std::bad_alloc{}; // 실제 구현은 wrap/fence chunk 정책
    }
    head_ = begin + bytes;
    return {
        mapped_ + begin,
        resource_->GetGPUVirtualAddress() + begin,
        begin,
        bytes
    };
}
```

constant buffer는 256-byte alignment를 적용한다. ring wrap은 이전 frame 영역의 fence 완료를 확인해야 한다.

## 119.5 문제 34: Descriptor와 Resource 수명

SRV descriptor slot을 다른 texture로 덮어도 원래 `ID3D12Resource` 객체는 살아 있을 수 있다. 반대로 descriptor가 아직 원래 resource를 가리키는데 resource를 파괴하면 GPU가 invalid VA를 접근할 수 있다. 둘 모두 마지막 GPU 사용 fence까지 유지한다.

## 119.6 문제 35: State tracker

```cpp
void StateTracker::Transition(ID3D12GraphicsCommandList* list,
                              ID3D12Resource* resource,
                              D3D12_RESOURCE_STATES after)
{
    auto& before = states_.at(resource);
    if (before == after) return;

    D3D12_RESOURCE_BARRIER b{};
    b.Type = D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
    b.Transition.pResource = resource;
    b.Transition.StateBefore = before;
    b.Transition.StateAfter = after;
    b.Transition.Subresource = D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
    list->ResourceBarrier(1, &b);
    before = after;
}
```

실전에서는 subresource별 state, split barrier, queue ownership, imported resource initial/final state가 필요하다.

## 119.7 문제 50: Render graph edge

resource마다 `lastWriter`와 `readersSinceWrite`를 유지한다.

```cpp
for (PassId p : passOrder) {
    for (Use u : passes[p].uses) {
        auto& s = resourceState[u.resource];
        if (u.read) {
            if (s.lastWriter) AddEdge(*s.lastWriter, p);
            s.readers.push_back(p);
        }
        if (u.write) {
            if (s.lastWriter) AddEdge(*s.lastWriter, p);
            for (PassId r : s.readers) AddEdge(r, p);
            s.readers.clear();
            s.lastWriter = p;
        }
    }
}
```

read-modify-write use를 중복 edge 없이 처리하고 pass 내부 동일 resource use를 normalize한다.

## 119.8 문제 51: Cycle 진단

Kahn topological sort에서 처리하지 못한 node가 cycle에 포함된다. 단순 “cycle 있음”보다 DFS parent를 사용해 실제 path를 출력한다.

```text
Lighting writes HDR
→ TAA reads HDR, writes History
→ Lighting incorrectly reads History as same-frame input
```

history resource는 frame 간 external/imported edge로 모델링한다.

## 119.9 문제 54: Transient aliasing

각 resource interval `[firstUse,lastUse]`가 겹치지 않으면 같은 heap region을 재사용할 수 있다. size/alignment/heap flags/format compatibility를 고려한 interval allocation을 수행하고 aliasing barrier를 넣는다.

```text
Depth   [0────────3]
AO          [2──4]
Bloom             [5──7]  ← Depth memory reuse 가능
```

## 119.10 문제 68: GGX NDF

```hlsl
float D_GGX(float NoH, float roughness)
{
    float a = max(roughness * roughness, 0.0025f);
    float a2 = a * a;
    float f = NoH * NoH * (a2 - 1.0f) + 1.0f;
    return a2 / max(PI * f * f, 1e-7f);
}
```

프로젝트가 `alpha=roughness²`, `a2=alpha²`인지 변수 이름을 명확히 한다. roughness를 두 번/네 번 제곱하는 혼동이 흔하다.

## 119.11 문제 72: White furnace

테스트 scene:

- environment radiance = 1
- direct light 없음
- material grid: metallic 0/1, roughness 0.05–1
- exposure/tone map 전에 linear HDR readback

검사:

```cpp
CHECK(maxRgb <= 1.02f);          // 작은 수치 오차 허용
CHECK(AllFinite(pixel));
CHECK(minRgb >= -1e-4f);
```

single-scattering GGX는 rough surface에서 에너지를 잃을 수 있으므로 “정확히 1”이 아닐 수 있다. 목적은 에너지 생성과 급격한 불연속 탐지다.

## 119.12 문제 75: Mirrored UV

vertex tangent의 `w`에 bitangent handedness를 저장한다.

```hlsl
float3 T = normalize(input.tangent.xyz);
float3 B = normalize(cross(N, T)) * input.tangent.w;
float3 worldN = normalize(nTS.x*T + nTS.y*B + nTS.z*N);
```

importer와 normal-map baker가 같은 tangent convention을 사용해야 한다.

## 119.13 문제 80: SH9

projection은 environment sample `L(ω)`에 basis `Y_lm(ω)`와 sample weight를 곱해 누적한다.

```cpp
for (Sample s : sphereSamples) {
    auto basis = EvaluateSHBasis9(s.direction);
    for (int i = 0; i < 9; ++i) {
        coeff[i] += s.radiance * basis[i] / s.pdf;
    }
}
for (auto& c : coeff) c /= sampleCount;
```

Lambert convolution coefficient를 projection 또는 evaluation 단계에 적용한다.

## 119.14 문제 92: Log cluster slice

```hlsl
uint ComputeClusterZ(float viewZ)
{
    float t = log2(max(viewZ, NearZ) / NearZ)
            / log2(FarZ / NearZ);
    return min((uint)(t * ClusterCountZ), ClusterCountZ - 1);
}
```

view-space z sign convention을 확인한다. `viewZ`는 양의 거리로 정규화해 전달하는 편이 안전하다.

## 119.15 문제 94: Count/scan/fill

세 pass:

1. 각 light가 겹치는 cluster count atomic increment
2. counts exclusive scan → offsets, total capacity check
3. cursor를 0으로 초기화하고 indices fill

이 구조는 overflow를 fill 전에 알 수 있다. atomic append 한 pass보다 memory가 늘 수 있으나 디버깅과 deterministic layout이 쉽다.

## 119.16 문제 98: Shadow bias

- constant bias: 모든 slope에 동일, 근거리/원거리 scale 문제
- slope bias: grazing surface acne 완화, 과하면 edge 분리
- normal offset: world-space surface 이동, silhouette/peter-panning

테스트는 수평면 하나가 아니라 steep slope, thin geometry, contact, cascade boundary를 포함한다.

## 119.17 문제 101: Cascade snapping

light-space cascade center를 texel 크기로 quantize한다.

```cpp
const float texel = (2.0f * radius) / resolution;
center.x = std::floor(center.x / texel) * texel;
center.y = std::floor(center.y / texel) * texel;
```

projection extent도 불필요하게 매 frame 변하지 않게 stable sphere fit 등을 사용한다.

## 119.18 문제 112: Motion vector

```hlsl
VSOut VSMain(VSIn input)
{
    float4 local = float4(input.position, 1);
    float4 world = mul(CurrentWorld, local);
    float4 prevWorld = mul(PreviousWorld, local);

    o.position = mul(CurrentViewProjectionJittered, world);
    o.currentClip = mul(CurrentViewProjectionUnjittered, world);
    o.previousClip = mul(PreviousViewProjectionUnjittered, prevWorld);
    return o;
}
```

jitter를 velocity에 포함할지 제거할지는 TAA convention과 일치해야 한다. 일반적으로 unjittered clip로 physical motion을 계산하고 resolve에서 jitter offset을 알고 처리한다.

## 119.19 문제 113: Depth rejection

current world position을 previous clip에 투영해 expected previous depth를 얻고 sampled previous depth와 비교한다. 단순 current/previous raw depth 차이는 projection과 motion 때문에 부정확하다.

## 119.20 문제 121: Generation handle

```cpp
Entity EntityPool::Create()
{
    uint32_t index;
    if (!free_.empty()) {
        index = free_.back();
        free_.pop_back();
    } else {
        index = static_cast<uint32_t>(generation_.size());
        generation_.push_back(1);
        alive_.push_back(false);
    }
    alive_[index] = true;
    return {index, generation_[index]};
}

bool EntityPool::Destroy(Entity e)
{
    if (!IsAlive(e)) return false;
    alive_[e.index] = false;
    ++generation_[e.index];
    free_.push_back(e.index);
    return true;
}
```

## 119.21 문제 122: Sparse set remove

```cpp
void Remove(Entity e)
{
    uint32_t i = sparse_[e.index];
    uint32_t last = static_cast<uint32_t>(dense_.size() - 1);

    dense_[i] = std::move(dense_[last]);
    entities_[i] = entities_[last];
    sparse_[entities_[i].index] = i;

    dense_.pop_back();
    entities_.pop_back();
    sparse_[e.index] = Invalid;
}
```

`dense_[i]` 주소가 바뀌므로 component pointer 장기 보관을 금지하거나 stable storage를 선택한다.

## 119.22 문제 127: Work stealing skeleton

```cpp
void WorkerLoop(uint32_t workerIndex)
{
    while (!stop_.load(std::memory_order_acquire)) {
        Job job;
        if (local_[workerIndex].PopBottom(job)
            || global_.TryPop(job)
            || Steal(workerIndex, job)) {
            Execute(job);
        } else {
            semaphore_.acquire();
        }
    }
}
```

실제 lock-free deque는 검증된 알고리즘을 사용하거나 mutex deque로 시작한다. 종료, wake-up lost signal, external submission을 테스트한다.

## 119.23 문제 135: Two-phase publication

```text
background compile/decode complete
→ render thread creates/uploads new GPU object
→ copy/graphics fence reaches ready value
→ atomic/locked handle slot swap
→ old object retired at its last-use fence
```

새 object가 ready 되기 전에 publish하거나 old object를 publish 시점에 파괴하면 안 된다.

## 119.24 문제 148: Hierarchical scan

```text
Pass A: each block scans local elements, writes block sum
Pass B: scan block sums
Pass C: add scanned block offset to each local result
```

block size가 고정일 때 shared memory bank conflict와 out-of-range lane을 처리한다.

## 119.25 문제 151: Async compute 실험

결론을 pass 이름으로 미리 정하지 않는다. 보고서:

```text
Baseline total GPU: 14.8 ms
AO graphics: 1.6 ms
AO async duration: 1.9 ms
Overlap with shadows: 1.2 ms
New total GPU: 13.9 ms
Bandwidth contention: lighting +0.3 ms
Net gain: 0.9 ms
```

## 119.26 문제 158: TLAS update

- static geometry BLAS: build + compact
- skinned/deformed BLAS: refit/update 또는 rebuild 비용 비교
- TLAS: instance transform/visibility 변화 시 update
- scratch/result lifetime와 build flags 저장
- build completion barrier/sync 후 trace

## 119.27 문제 161: Ray history validation

TAA와 유사하지만 ray signal의 hit distance, normal, material/instance ID, roughness를 추가로 비교한다. reflection은 화면 motion뿐 아니라 hit point motion도 고려한다.

## 119.28 문제 165: Reservoir sampling

candidate weight 합 `W`를 갱신하고 확률 `w_i/W`로 선택한다. 최종 estimator에는 target/proposal과 sample count에 따른 normalization이 필요하다. 단순 reservoir update만 구현하고 ReSTIR를 완성했다고 부르면 안 된다.

## 119.29 문제 171: Percentile

```cpp
double Percentile(std::vector<double> values, double p)
{
    if (values.empty()) return 0;
    std::sort(values.begin(), values.end());
    double x = p * (values.size() - 1);
    size_t i = static_cast<size_t>(x);
    size_t j = std::min(i + 1, values.size() - 1);
    return std::lerp(values[i], values[j], x - i);
}
```

production telemetry는 전체 sort 대신 histogram/t-digest 등을 고려한다.

## 119.30 문제 187: Fence와 Barrier

- **Fence:** queue/CPU 사이의 실행 완료 시점과 순서를 나타낸다. 다른 queue wait와 CPU wait에 사용한다.
- **Barrier:** 한 resource의 이전/다음 access 사이 visibility, ordering, layout/state transition을 정의한다.

barrier를 넣어도 다른 queue가 아직 작업 중이면 fence/wait가 필요하고, fence만 기다려도 올바른 resource state/access barrier가 필요할 수 있다.

# 120. 자기 채점 기준

각 문제를 0–4로 평가한다.

| 점수 | 기준 |
|---:|---|
| 0 | 모름 |
| 1 | 설명을 보면 이해 |
| 2 | 예제를 따라 구현 |
| 3 | 책 없이 구현하고 실패를 디버깅 |
| 4 | 변형 요구·성능·트레이드오프까지 설명 |

취업 포트폴리오 기준:

- A–C 평균 3 이상
- D–F 평균 2.5 이상
- H의 면접 문제 70% 이상을 자신의 코드와 연결
- 선택 전문 분야 한 묶음은 평균 3 이상
