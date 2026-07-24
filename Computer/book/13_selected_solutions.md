# 부록 B — 핵심 문제 해설과 자기평가 기준

이 해설은 정답을 복사하는 용도가 아니다. 먼저 자신의 답을 commit하고, test와 측정 결과를 보존한 뒤 비교한다. 구현 문제는 같은 계약을 만족하는 여러 답이 가능하다.

# 1. 역사와 계산

## 문제 2 — 인과 연표

좋은 답은 사건을 날짜순으로만 나열하지 않는다.

```text
Boole: 논리를 대수로 표현
→ Shannon: Boolean algebra를 switching circuit 분석에 연결
→ Turing: 계산 절차를 형식적 machine으로 모델링
→ stored program: 명령과 데이터를 memory에 표현
→ transistor/IC: 회로의 크기·전력·신뢰성 개선
→ microprocessor: CPU를 집적해 범용 계산의 비용 감소
```

Babbage는 programmable mechanical machine의 설계를, von Neumann 계열 보고서는 electronic stored-program organization의 구체화를 보여준다. 각 연결에서 “이전 한계”와 “새 trade-off”를 한 줄씩 적으면 4등급 답이다.

## 문제 9 — Turing 논문 카드

핵심:

- 문제: 효과적으로 계산 가능한 수/절차를 형식화
- 모델: 유한 상태 제어, 무한 tape, symbol read/write, head movement
- 아이디어: universal machine이 다른 machine의 description을 해석
- 결과: 계산 가능성의 한계와 decision problem 연결
- 주의: 실제 CPU의 성능·memory hierarchy 모델이 아님

논문에서 직접 확인한 section/page를 기록하고 현대 해설과 구분한다.

## 문제 13 — latency 0인 분산 시스템

latency가 0이어도 다음은 남는다.

- node crash와 독립 실패
- message loss/corruption 또는 network partition의 모델
- concurrent operation의 순서
- replicated state의 합의
- Byzantine/권한 문제
- deployment/version 차이

“원격 호출 비용이 0이면 local과 같다”는 주장은 **독립 failure와 state 복제**를 무시한다.

## 문제 25 — halting problem 스케치

어떤 프로그램 `P`와 입력 `x`가 멈추는지 항상 판정하는 `H(P,x)`가 있다고 가정한다. 다음 프로그램 `D(P)`를 만든다.

```text
if H(P, P) says halt:
    loop forever
else:
    halt
```

`D(D)`를 물으면 어느 답도 모순이다. 핵심은 단순 무한 loop 예가 아니라 **판정기를 자기 자신에게 적용하는 대각화**다.

# 2. 비트와 구조

## 문제 27 — 0x80과 0xFF

| pattern | unsigned | 8-bit two's complement |
|---|---:|---:|
| `0x80` | 128 | -128 |
| `0xFF` | 255 | -1 |

bit pattern 자체에는 type이 없다. 해석 규칙이 값을 정한다.

## 문제 28 — flag 계산

```cpp
struct Add8 {
    std::uint8_t value;
    bool carry;
    bool overflow;
    bool zero;
    bool negative;
};

Add8 add8(std::uint8_t a, std::uint8_t b) {
    const std::uint16_t wide = static_cast<std::uint16_t>(a) + b;
    const auto value = static_cast<std::uint8_t>(wide);
    const bool overflow = ((~(a ^ b) & (a ^ value)) & 0x80u) != 0;
    return {value, wide > 0xFFu, overflow, value == 0,
            (value & 0x80u) != 0};
}
```

필수 test:

```text
0xFF + 0x01 = 0x00, carry=1, overflow=0
0x7F + 0x01 = 0x80, carry=0, overflow=1
0x80 + 0x80 = 0x00, carry=1, overflow=1
```

## 문제 31 — endian parser

```cpp
expected<std::uint32_t, ParseError>
read_u32_le(std::span<const std::byte> bytes, std::size_t offset) {
    if (offset > bytes.size() || bytes.size() - offset < 4) {
        return unexpected(ParseError::Truncated);
    }
    auto u = [&](std::size_t i) {
        return std::to_integer<std::uint32_t>(bytes[offset + i]);
    };
    return u(0) | (u(1) << 8) | (u(2) << 16) | (u(3) << 24);
}
```

`reinterpret_cast<uint32_t*>`는 alignment, endian, aliasing 문제를 만들 수 있다.

## 문제 43 — calling convention

답에 포함할 것:

- argument를 register/stack 어디에 둘지
- return value
- caller/callee-saved register
- stack alignment
- name mangling와 object layout
- exception unwinding/debug info

서로 따로 compile된 caller와 callee가 같은 규칙을 공유해야 binary가 연결된다.

## 문제 49 — false sharing

서로 다른 atomic이 같은 cache line에 있으면 각 write가 cache coherence ownership을 이동시킨다. 논리적 데이터 공유가 없어도 line 단위로 ping-pong한다.

검증:

```cpp
struct alignas(64) Counter { std::atomic<std::uint64_t> value{}; };
```

alignment 전후를 여러 core에서 반복하고 hardware topology와 line size를 기록한다. `alignas(64)`가 모든 하드웨어에 보편적 정답이라는 뜻은 아니다.

# 3. 운영체제와 동시성

## 문제 59 — condition variable의 `if`

spurious wakeup 또는 다른 consumer가 먼저 item을 가져갈 수 있다.

```cpp
std::unique_lock lock(mutex_);
cv_.wait(lock, [&] { return closed_ || !queue_.empty(); });
if (queue_.empty()) return std::nullopt;
auto value = std::move(queue_.front());
queue_.pop();
return value;
```

predicate는 lock 아래에서 검사한다.

## 문제 60 — data race와 race condition

- data race: C++ memory model에서 동기화 없이 같은 memory location에 충돌 접근, 적어도 하나 write. UB.
- race condition: 실행 순서에 따라 논리 결과가 달라지는 더 넓은 개념. atomic만 사용해 data race가 없어도 check-then-act race가 가능.

```cpp
if (balance.load() >= 10) balance.fetch_sub(10);
```

두 thread가 모두 조건을 통과할 수 있다.

## 문제 62 — acquire/release

producer:

```cpp
data = make_data();
ready.store(true, std::memory_order_release);
```

consumer:

```cpp
if (ready.load(std::memory_order_acquire)) {
    use(data);
}
```

acquire가 release 값을 읽으면 release 이전 write가 consumer에서 visible한 happens-before 관계를 만든다. `data` 자체를 atomic으로 만들지 않아도 이 특정 publish protocol 아래에서는 안전하다.

## 문제 66 — deadlock 조건

1. mutual exclusion
2. hold and wait
3. no preemption
4. circular wait

lock ordering은 circular wait를 제거한다.

```text
항상 WorldLock → InventoryLock → LogLock 순서
```

`std::scoped_lock(a,b)`처럼 deadlock avoidance를 제공하는 도구도 검토한다.

## 문제 72 — WAL 순서

일반 원칙:

```text
log record durable
→ data page write 가능
→ commit record durable
→ 성공 응답
```

구체 DB에 따라 protocol은 다르지만, 복구가 data page보다 먼저 그 변경의 log를 볼 수 있어야 한다. 성공 응답의 durability가 OS cache인지 stable storage인지 명시한다.

# 4. 언어와 컴파일러

## 문제 79 — lexical vs dynamic scope

```text
let x = 1;
fn f() { print(x); }
fn g() { let x = 2; f(); }
g();
```

lexical scope는 `f` 정의 위치의 `x=1`, dynamic scope는 호출 stack의 `x=2`를 찾는다. 대부분의 현대 범용 언어는 lexical scope를 사용한다.

## 문제 81 — precedence parser

recursive descent의 핵심:

```text
expression → term (("+" | "-") term)*
term       → unary (("*" | "/") unary)*
unary      → "-" unary | primary
primary    → NUMBER | "(" expression ")"
```

각 함수가 자신보다 강한 precedence를 호출한다. `1-2-3`은 loop로 left associative가 된다.

## 문제 87 — closure lifetime

outer stack frame가 사라져도 capture가 살아야 한다. open upvalue가 stack slot을 가리키다가 function return 때 heap cell로 닫히는 구현을 사용할 수 있다.

```text
stack local n
  ↑ open upvalue
return
  ↓ copy/move to heap cell
closure → cell
```

GC root에 closure와 open upvalue를 포함한다.

## 문제 90 — bytecode verifier

검사:

- opcode 유효
- operand/constant index 범위
- instruction boundary
- jump target이 instruction 시작
- 모든 control-flow path의 stack depth 일치
- stack under/overflow
- function signature와 call arity

비신뢰 bytecode는 VM 실행 전에 검증한다.

## 문제 96 — SSA phi

```text
if cond: x = 1
else:    x = 2
print(x)
```

merge block에서 하나의 SSA 이름이 필요하다.

```text
x1 = 1
x2 = 2
x3 = phi(x1 from then, x2 from else)
```

phi는 runtime 함수라기보다 predecessor에 따라 값을 선택하는 IR 표현이다.

## 문제 100 — UB와 optimizer

signed integer overflow가 없다고 language가 규정하므로 compiler는 `x + 1 > x`를 참으로 단순화할 수 있다. 실제 hardware wraparound를 기대한 코드는 language contract를 위반한다. unsigned 또는 checked arithmetic을 사용한다.

# 5. 알고리즘

## 문제 105 — insertion sort invariant

outer loop index `i` 시작 시 `A[0..i)`가 정렬되어 있고 원래 같은 원소 multiset을 가진다는 불변식을 둔다.

- 초기: 길이 1 이하 prefix는 정렬
- 유지: `A[i]`를 적절한 위치까지 이동해 `A[0..i+1)` 정렬
- 종료: `i=n`, 전체 정렬

정렬 순서뿐 아니라 원소 보존도 증명해야 한다.

## 문제 109 — hash tombstone

open addressing에서 삭제 slot을 Empty로 바꾸면 probe chain이 끊겨 뒤의 key를 못 찾는다. `Tombstone` 상태를 두고 lookup은 계속, insertion은 재사용한다. tombstone 비율이 높으면 rehash한다.

## 문제 116 — binary search

half-open `[lo, hi)`:

```cpp
while (lo < hi) {
    const auto mid = lo + (hi - lo) / 2;
    if (a[mid] < key) lo = mid + 1;
    else hi = mid;
}
```

종료 후 `lo`는 lower_bound. 불변식은 `[0,lo)`가 key보다 작고 `[hi,n)`가 key 이상이라는 식으로 정의할 수 있다.

## 문제 119 — A*

`f=g+h`. heuristic가 실제 남은 비용을 초과하지 않으면 admissible. consistent하면 재개방 없이 graph search가 단순해진다. grid에서 Manhattan은 4방향 unit cost에 적합하지만 diagonal을 허용할 때는 다른 heuristic이 필요하다.

## 문제 123 — Bloom filter

- false positive 가능: 여러 key의 bit가 우연히 모두 set
- false negative 없음: 삽입된 key의 bit를 삭제하지 않는 표준 구조

counting Bloom처럼 삭제를 넣으면 counter overflow/underflow 정책이 필요하다.

# 6. 네트워크와 분산

## 문제 131 — TCP framing

한 `send`의 100 byte가 상대에서 `recv` 40+60으로 오거나 여러 send가 한 recv에 합쳐질 수 있다. decoder는 buffer에 누적해 header가 충분한지, 선언 payload가 충분한지 확인하고 남은 byte를 보존한다.

## 문제 136 — timeout 중복

```text
client sends purchase id=K
server commits purchase
response lost
client times out and retries K
```

idempotency table:

```text
(K, principal, operation hash, result, status)
```

같은 K와 같은 operation이면 저장된 결과 반환. 다른 payload면 오류. table retention과 concurrent duplicate를 transaction으로 처리한다.

## 문제 143 — write skew

두 의사가 on-call이라고 가정하고 각 transaction이 다른 의사가 남아 있음을 읽은 뒤 자신을 off-call로 변경하면, snapshot isolation 아래 둘 다 commit해 0명이 될 수 있다. constraint를 하나의 row/counter에 잠그거나 serializable isolation/명시적 lock을 사용한다.

## 문제 148 — Lamport clock

`a→b`이면 clock update 규칙상 `L(a)<L(b)`. 그러나 서로 concurrent인 사건에도 임의 node counter 때문에 `L(a)<L(b)`가 될 수 있어 역은 성립하지 않는다. vector clock은 component-wise 비교로 concurrency를 더 표현한다.

## 문제 153 — CAP

partition이 발생해 노드 간 통신이 끊겼을 때:

- availability를 유지해 양쪽 요청에 응답하면 서로 다른 상태를 허용할 수 있다.
- 강한 consistency를 유지하려면 적어도 한쪽 요청을 거부/대기시킬 수 있다.

정상 시점의 latency/consistency 선택 전체를 CAP 한 문장으로 설명하지 않는다.

## 문제 154 — Raft simulator 핵심

상태:

```text
currentTerm, votedFor, log[], commitIndex, role
```

invariant 예:

- term 단조 증가
- 한 node는 term당 한 표
- committed entry는 이후 leader log에 존재
- 같은 index/term이면 prefix 일치

random event보다 deterministic queue와 seed를 사용해 반례를 재현한다.

# 7. 아키텍처

## 문제 164 — 상태 머신

상태 전이를 한 장소에서 검증한다.

```cpp
bool StateMachine::request(Event e) {
    auto t = table_.find({current_, e});
    if (!t) return false;
    if (current_ == State::Dead) return false;
    if (!guards_pass(*t)) return false;
    exit(current_);
    current_ = t->to;
    enter(current_);
    return true;
}
```

Stun과 death 같은 high-priority event가 animation end보다 먼저 처리되는 ordering을 test한다.

## 문제 170 — generation handle

```cpp
struct Handle { std::uint32_t index, generation; };

void destroy(Handle h) {
    auto& slot = slots.at(h.index);
    if (!slot.alive || slot.generation != h.generation) return;
    slot.value.reset();
    slot.alive = false;
    ++slot.generation;
    free.push_back(h.index);
}
```

삭제 후 같은 index 재사용 시 이전 handle의 generation이 달라 `try_get`이 null이다. generation wrap과 invalid sentinel을 문서화한다.

## 문제 172 — fixed timestep

필수:

- frame delta clamp
- accumulator
- 최대 simulation step 또는 overload 정책
- previous/current state
- interpolation alpha

simulation에 raw wall-clock를 다시 읽으면 determinism이 깨진다.

## 문제 175 — system DAG

edge `A→B`는 B가 A 결과를 필요로 함을 뜻한다. Kahn topological sort에서 처리 node 수가 전체보다 작으면 cycle. cycle을 발견했을 때 무조건 event로 바꾸지 말고 같은 phase에 합칠지, 다음 tick으로 지연할지 불변식을 검토한다.

## 문제 178 — RenderSnapshot

snapshot에는 render가 필요한 값만 복사한다.

```cpp
struct RenderItem { Mat4 world; MeshId mesh; MaterialId material; };
```

world pointer, gameplay component reference를 넣지 않는다. lifetime은 frame allocator와 fence/consumer 완료까지 명시한다. 추출 시간과 bytes를 측정한다.

# 8. 품질과 성능

## 문제 184 — sort property

1. ordered
2. permutation/multiset preservation
3. idempotent
4. stable sort라면 equal-key relative order

실패 input을 shrink해 최소 반례를 보존한다.

## 문제 190 — bug report

합격 기준:

- 기대/실제 분리
- 5단계 이하 최소 재현
- 재현율
- environment/build ID
- 최초 정상/최초 실패
- artifact(log, input, dump)
- 민감 정보 제거

## 문제 199 — Amdahl

후보마다 전체 비율 `p`를 profiler에서 얻어야 한다. `p=0.4`, 부분 speedup `s=4`라면:

```text
1 / (0.6 + 0.4/4) = 1.428...
```

부분 함수 benchmark의 4배를 전체 4배라고 보고하지 않는다.

## 문제 200 — Roofline

예: kernel이 원소당 8 FLOP와 16 byte read/write를 하면 arithmetic intensity는 약 `0.5 FLOP/byte`. 장치 bandwidth가 400 GB/s면 bandwidth roof는 200 GFLOP/s. compute peak가 10 TFLOP/s여도 이 kernel은 대역폭 제한 가능성이 높다.

실제 cache reuse와 write allocation을 포함해 추정 범위를 쓴다.

## 문제 203 — GPU 병목 실험

- 해상도 절반: pixel/RT bandwidth 비용이 크면 개선
- draw count 감소: CPU submit/state change가 크면 개선
- shader를 상수 출력: shader ALU/texture가 크면 개선

한 실험으로 확정하지 않고 capture counters와 결합한다.

# 9. 보안과 신뢰성

## 문제 209 — 위협 모델

최소 산출물:

```text
asset: credential, inventory, payment, availability
actor: player, attacker, admin, build system
boundary: device/server, gateway/service, service/DB, CI/release
```

각 boundary의 인증·암호화·검증·logging·rate limit을 적고 남은 위험을 수용/완화/전가/회피로 분류한다.

## 문제 216 — parser 제한

길이를 곱하기 전에 overflow를 검사한다.

```cpp
if (count > max_count || element_size > max_bytes / count) reject;
```

재귀 parser는 depth budget, 전체 node budget, deadline을 공유한다. 각 nested call이 새로운 무제한 budget을 만들면 안 된다.

## 문제 220 — client damage

client는 `target=7, damage=99999` 사실을 보내지 않고 `fire(input sequence, aim)` 의도를 보낸다. 서버가 cooldown, ammo, position history, hit, damage를 검증한다. prediction visual은 local에서 가능하지만 authoritative inventory/health는 server correction을 따른다.

## 문제 229 — overload

unbounded queue에서 service time보다 arrival가 크면 queue와 latency가 계속 증가한다. client timeout/retry가 arrival를 더 높인다. 해결은 bounded queue, concurrency limit, deadline-aware rejection, retry-after/jitter, optional work shedding이다. 성공률뿐 아니라 rejected와 timed-out 요청을 분리해 측정한다.

## 문제 230 — restore test

백업 파일 존재가 아니라 새 환경에서:

1. credential/key 확보
2. restore
3. schema/version migration
4. consistency check
5. application smoke
6. RPO/RTO 측정

자동화하고 production과 권한 failure domain을 분리한다.

# 10. 게임·그래픽스·AI

## 문제 241 — MVP 변환

열벡터 관례에서:

```text
p_clip = P · V · M · p_local
p_ndc = p_clip.xyz / p_clip.w
p_screen = viewport(p_ndc)
```

답에는 자신의 engine이 row/column major와 multiplication convention을 어떻게 쓰는지 포함해야 한다. transpose를 무조건 넣는 것은 해결이 아니다.

## 문제 243 — CPU rasterizer

핵심:

- triangle bounding box
- edge function/barycentric
- winding와 inside rule
- depth interpolation/test
- perspective-correct varying
- viewport clipping

reference image와 작은 triangle, degenerate, screen edge를 test한다.

## 문제 245 — BRDF 비교

Lambert는 diffuse만. Blinn-Phong은 경험적 highlight. microfacet GGX는 normal distribution, Fresnel, masking-shadowing을 분리한다. PBR이라고 부르려면 단순 식 복사보다 input 색공간, normalization, energy conservation을 검증한다.

## 문제 251 — GPU resource lifetime

CPU handle destructor 시점과 GPU 완료 시점이 다르다. command submission과 연관된 fence value까지 resource를 retire queue에 보존하고 completed fence 후 해제한다. descriptor reuse도 같은 문제를 갖는다.

## 문제 254 — prediction/reconciliation

```text
client stores inputs 101..104
server snapshot acknowledges 102
client sets state=server state at 102
reapplies 103,104
```

각 input에 sequence와 fixed tick이 필요하다. correction error, replay 비용, visual smoothing을 측정한다.

## 문제 257 — behavior tree cancellation

`MoveTo`가 running인 동안 상위 condition이 바뀌면 abort/cancel이 하위 navigation request를 해제해야 한다. node lifetime과 callback token을 관리한다. 실행 trace에는 tick, node, status transition, reason을 기록한다.

## 문제 260 — AI 생성 코드 검증

합격 pipeline:

```text
명세와 threat/lifetime 가정
→ isolated branch
→ compile warnings/static analysis
→ unit/property/fuzz/sanitizer
→ benchmark와 visual regression
→ human review
→ provenance/라이선스 정책
```

“AI가 작성했다”도 “AI라서 틀렸다”도 증거가 아니다. 같은 engineering gate를 적용한다.

# 통합 문제 평가 기준

통합 문제는 다음 8축으로 각 0–5점을 준다.

| 축 | 0 | 3 | 5 |
|---|---|---|---|
| 명세 | 목표 없음 | 기능/제약 | 불변식·비목표·실패 모델 |
| 정확성 | 수동 실행 | unit/integration | property/fuzz/model/fault |
| 수명 | 불명확 | RAII/handle | async/GPU/network까지 trace |
| 구조 | 전역 결합 | 모듈 | 변경 실험과 ADR |
| 성능 | 느낌 | profiler | 비용 모델·분포·회귀 gate |
| 보안 | 미고려 | 입력/권한 | 위협 모델·공급망·복구 |
| 문서 | 없음 | README | 사양·결정·한계·재현 |
| 설명 | 용어 나열 | 구현 설명 | 대안·반례·계층 연결 |

총점 24 미만이면 기능을 늘리지 말고 기반을 보완한다. 32 이상은 취업 포트폴리오 후보, 36 이상은 다른 사람이 재현·review 가능한 수준을 목표로 한다. 점수는 자기 위안을 위한 숫자가 아니라 누락을 찾는 checklist다.
