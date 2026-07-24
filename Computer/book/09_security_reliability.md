# 제9부 — 보안, 신뢰성, 실패를 전제로 한 설계

# 47장. 보안의 시작: 자산, 신뢰 경계, 공격자의 능력

## 47.1 보안은 기능 목록이 아니라 보장 범위다

“암호화를 사용한다”는 보안 설계가 아니다. 다음을 먼저 정의한다.

- 보호할 자산: 계정, 결제, 소스, save data, 개인 정보, service availability
- 공격자: 일반 사용자, 악성 클라이언트, 내부자, 공급망 침해자
- 능력: 패킷 수정, 파일 편집, process memory 읽기, admin 권한, physical access
- 신뢰 경계: client/server, plugin/host, user/kernel, build/package
- 허용 손실과 복구 시간

게임 클라이언트는 사용자 장치에서 실행된다. 사용자가 binary와 memory를 통제할 수 있다고 가정해야 한다. 중요한 경제 불변식을 클라이언트 판정만으로 보호할 수 없다.

## 47.2 위협 모델

간단한 데이터 흐름도:

```text
[Player Client] --TLS--> [API Gateway] --> [Game Service] --> [Database]
      |                         |
  local save                admin console
```

각 화살표와 저장소에서 묻는다.

- 누가 신원을 주장하는가?
- 입력을 변조할 수 있는가?
- 재전송할 수 있는가?
- 민감한 정보가 노출되는가?
- service를 고갈시킬 수 있는가?
- 감사 가능한가?

STRIDE는 누락을 줄이는 체크리스트다.

| 범주 | 질문 |
|---|---|
| Spoofing | 다른 주체로 가장할 수 있는가? |
| Tampering | 데이터·코드를 바꿀 수 있는가? |
| Repudiation | 행위를 부인할 수 있는가? |
| Information disclosure | 비밀이 노출되는가? |
| Denial of service | 자원을 고갈시킬 수 있는가? |
| Elevation of privilege | 더 큰 권한을 얻는가? |

## 47.3 Saltzer와 Schroeder의 보호 원칙

고전 논문은 보안 메커니즘의 설계 원칙을 정리했다. [[The Protection of Information in Computer Systems, 1975](https://web.mit.edu/Saltzer/www/publications/protection/)]

### 최소 권한

작업에 필요한 최소 권한만, 필요한 시간 동안 부여한다.

```text
asset converter: source asset 읽기 + output directory 쓰기
필요 없음: user home 전체, production credential, network admin
```

### fail-safe defaults

허용 목록에 없으면 거부한다.

```cpp
if (!policy.allows(user, Action::DeleteSave, save_id)) {
    return unexpected(AuthError::Denied);
}
```

오류 시 권한을 넓히지 않는다.

### 완전한 중재

모든 접근을 검사한다. 첫 요청에서만 검사하고 오래된 권한을 cache하면 철회가 반영되지 않을 수 있다.

### 개방 설계

알고리즘 비밀보다 key 비밀에 의존한다. 공격자가 구조를 안다고 가정해도 안전해야 한다.

### 권한 분리

중요 작업에 둘 이상의 조건을 요구한다.

```text
production deploy = 승인된 commit + CI 서명 + 사람 승인
```

### 최소 공통 메커니즘

여러 사용자·tenant가 공유하는 상태를 줄여 정보 누출과 결합을 줄인다.

## 47.4 인증과 권한

인증은 누구인지, 권한은 무엇을 할 수 있는지다.

나쁜 구조:

```cpp
if (request.user_id == resource.owner_id) allow();
```

`user_id`가 client body에서 온다면 위조 가능하다. 인증된 credential에서 principal을 얻고 resource/action 정책을 평가한다.

```cpp
Principal principal = auth.verify(request.credential);
authorizer.require(principal, Action::ReadInventory, resource);
```

권한 모델:

- ACL
- RBAC
- ABAC
- capability

복잡한 role만 늘리면 role explosion이 생긴다. 실제 정책과 감사 요구에 맞춘다.

## 47.5 비밀번호와 credential

비밀번호는 복호화 가능한 암호문이 아니라 salt가 있는 password hashing으로 저장한다. 직접 암호 알고리즘을 만들지 않는다.

credential 원칙:

- source code에 넣지 않음
- log에 출력하지 않음
- 최소 scope
- 짧은 lifetime
- rotation
- secret manager
- 개발·운영 분리
- 유출 가정과 폐기 절차

## 47.6 암호학 경계

암호학은 primitive보다 protocol이 어렵다.

- encryption만으로 integrity가 생기지 않음
- nonce 재사용 위험
- key distribution
- replay
- downgrade
- certificate validation
- random source
- side channel

검증된 TLS와 표준 라이브러리를 사용한다. 암호화를 붙이기 전에 위협 모델과 key lifecycle을 쓴다.

## 47.7 입력 검증과 parser

모든 외부 입력은 공격 표면이다.

```cpp
expected<Message, ParseError> parse(Buffer bytes) {
    Reader r(bytes);
    const auto length = TRY(r.u32_be());
    if (length > kMaxPayload) return unexpected(ParseError::TooLarge);
    return parse_payload(TRY(r.bytes(length)), /*depth=*/0);
}
```

검증 항목:

- 길이와 정수 overflow
- UTF-8과 canonical form
- 중첩 깊이
- 압축 폭탄
- path traversal
- symbolic link
- zip entry path
- regex complexity
- timeout
- memory budget

파일 경로:

```text
user input: ../../startup/config
```

문자열 prefix 검사만으로 path containment를 보장하지 못한다. canonicalization, root-relative open, platform API를 사용하고 symlink race를 고려한다.

## 47.8 injection

SQL:

```cpp
// 금지: 문자열 결합
query("SELECT * FROM player WHERE name='" + name + "'");

// parameter binding
stmt.bind(1, name);
```

명령어, HTML, template, log에도 각 문맥의 encoding이 필요하다. 입력을 무조건 제거하는 것보다 구조화 API로 code와 data를 분리한다.

## 47.9 client 보안과 게임 치트

클라이언트에서 다음을 완전히 숨기거나 신뢰할 수 없다.

- 비밀 key
- damage 판정
- inventory 잔액
- anti-cheat 탐지 로직
- 아직 공개되지 않은 asset

서버 권위 모델:

```text
client: input intent와 prediction
server: 검증, authoritative state transition
client: reconciliation와 interpolation
```

그러나 서버 검증이 모든 행동을 느리게 만들지 않도록 latency budget과 prediction을 설계한다.

<div class="lab">

### 실습: 게임 로그인과 구매 위협 모델

다음을 작성한다.

1. data flow diagram
2. 자산과 공격자
3. 20개 위협
4. 각 위협의 likelihood/impact
5. 예방·탐지·복구 통제
6. 남은 위험
7. security test

특히 token 탈취, request replay, price tampering, duplicate purchase, log secret, admin privilege를 다룬다.

</div>

# 48장. 메모리 안전, 공급망, 격리

## 48.1 메모리 안전 결함

C/C++에서 대표적인 결함:

- out-of-bounds
- use-after-free
- double free
- uninitialized read
- integer overflow 후 작은 allocation
- format string
- type confusion
- data race

```cpp
std::uint32_t count = read_u32(input);
const std::size_t bytes = count * sizeof(Vertex); // overflow 가능
void* p = std::malloc(bytes);
read(input, p, count * sizeof(Vertex));
```

검사:

```cpp
if (count > kMaxVertices ||
    count > std::numeric_limits<std::size_t>::max() / sizeof(Vertex)) {
    return unexpected(ParseError::TooLarge);
}
```

## 48.2 언어와 안전성 경계

Rust 같은 언어는 ownership과 borrowing 규칙으로 많은 memory safety 오류를 compile time에 제한한다. 그러나 `unsafe`, FFI, 논리 오류, resource exhaustion은 남는다. [[The Rust Reference: Behavior considered undefined](https://doc.rust-lang.org/reference/behavior-considered-undefined.html)]

C++에서 위험을 낮추는 방법:

- RAII
- bounds-aware view
- value type
- `unique_ptr` 기본
- raw owning pointer 금지
- sanitizer
- warnings as errors의 선택적 적용
- fuzzing
- 위험 parser를 memory-safe process로 분리

언어 논쟁보다 **위험한 입력과 권한이 있는 코드를 어디에 격리할지**가 중요하다.

## 48.3 sandbox와 process boundary

비신뢰 plugin이나 asset importer는 별도 process에서 제한할 수 있다.

```text
Editor ──restricted IPC──> Import Worker
                           - no production credentials
                           - limited filesystem
                           - memory/time limit
                           - kill on timeout
```

process 분리는 serialization과 latency 비용이 있지만 crash와 권한을 격리한다.

## 48.4 dependency 공급망

dependency는 코드와 함께 위험을 가져온다.

검토:

- 누가 유지하는가?
- release와 commit 서명
- transitive dependency
- 알려진 취약점
- 설치 script
- network access
- update 정책
- license
- abandoned project

버전을 lock하고 artifact hash를 검증한다. 그러나 오래 고정하면 취약점 수정이 들어오지 않는다. 자동 알림과 검토된 update cadence가 필요하다.

## 48.5 SBOM과 provenance

Software Bill of Materials는 제품에 포함된 component와 version을 추적한다. provenance는 artifact가 어떤 source, builder, command로 만들어졌는지 기록한다.

```text
artifact
- source commit
- build workflow identity
- compiler/container digest
- dependency lock digest
- tests
- signature
```

incident 시 영향받은 build를 빠르게 찾을 수 있다.

## 48.6 code signing과 update

자동 업데이트는 강력한 원격 코드 실행 채널이다.

필요한 성질:

- manifest와 payload 서명
- key rotation과 offline root
- rollback/downgrade 정책
- atomic install
- interrupted update recovery
- staged rollout
- revocation
- audit log

서명 검증 실패 시 “사용자 편의”를 위해 실행하지 않는다.

## 48.7 plugin과 mod

mod 지원 수준을 명확히 나눈다.

- 데이터만: 제한된 schema
- script: sandbox API와 instruction/memory budget
- native plugin: host와 같은 권한, 가장 위험

script API는 capability를 최소화한다.

```text
허용: spawn_visual_effect, query_nearby_entities
금지: arbitrary file, process, network, raw memory
```

## 48.8 보안 test

- parser fuzzing
- authorization negative test
- dependency scan
- secret scan
- static/dynamic analysis
- sandbox escape review
- update signature failure
- backup/restore permission
- rate limit/DoS load

penetration test는 설계·자동 test의 대체가 아니라 보완이다.

# 49장. 신뢰성 공학, 장애 주입, 복구, 윤리

## 49.1 장애와 결함을 구분한다

- fault: 잠재 원인
- error: 잘못된 내부 상태
- failure: 외부 계약 위반

예:

```text
disk sector fault → log record read error → service가 committed data를 반환 못함
```

설계는 fault가 곧 전체 failure가 되지 않도록 detection, redundancy, isolation, recovery를 둔다.

## 49.2 실패 모델

먼저 어떤 실패를 고려하는지 적는다.

- crash-stop
- crash-recovery
- omission/loss
- delay
- duplicate
- corruption
- Byzantine
- operator error
- overload

모든 실패를 동일하게 처리할 수 없다. 보장과 비용이 달라진다.

## 49.3 timeout, deadline, cancellation

각 계층이 독립 timeout을 길게 잡으면 전체 요청이 예상보다 오래 걸린다. 상위 deadline을 전파한다.

```cpp
Result fetch_profile(PlayerId id, Deadline deadline, CancellationToken stop);
```

남은 시간이 없으면 하위 요청을 시작하지 않는다. cancellation 후에도 이미 발생한 side effect는 사라지지 않으므로 결과 확인과 idempotency가 필요하다.

## 49.4 overload와 backpressure

무한 queue는 장애를 지연시킬 뿐이다.

```text
arrival rate > service rate
→ queue 증가
→ latency 증가
→ timeout과 retry
→ 더 큰 arrival rate
```

대응:

- bounded queue
- admission control
- load shedding
- priority
- retry budget
- concurrency limit
- degrade optional feature

Little의 법칙:

```text
L = λW
```

평균 시스템 내 요청 수 `L`, 도착률 `λ`, 체류 시간 `W`의 관계다. queue가 길어지면 latency가 필연적으로 증가한다.

## 49.5 redundancy와 공통 원인

replica가 많아도 같은 region, credential, software bug, deployment로 동시에 실패할 수 있다.

- failure domain 분리
- 독립적인 health signal
- staged rollout
- backup이 production 권한과 함께 삭제되지 않도록 분리
- 복구 연습

## 49.6 backup은 restore가 검증되어야 한다

backup checklist:

- 무엇을 포함하는가?
- encryption key도 복구 가능한가?
- retention과 삭제 정책
- RPO: 허용 데이터 손실 시간
- RTO: 복구 시간 목표
- 정기 restore test
- corrupted backup 탐지

“백업 job 성공”과 “서비스 복구 가능”은 다르다.

## 49.7 chaos와 fault injection

production chaos는 준비 없이 서버를 끄는 행위가 아니다.

과정:

1. 정상 상태와 SLO 정의
2. 작은 blast radius
3. 자동 중단 조건
4. 단일 가설
5. 관찰
6. 개선과 반복

개발 환경 fault injection:

- N번째 allocation 실패
- file write 일부만 성공
- `fsync` 실패
- packet drop/duplicate/delay
- clock jump
- thread pause
- GPU device removal
- corrupted asset

## 49.8 graceful degradation

핵심 기능과 부가 기능을 분리한다.

```text
로그인: 핵심
친구 추천: 부가
상점 배너: 부가
결제 기록: 핵심
```

추천 service 장애가 로그인 전체를 막지 않게 timeout과 fallback을 둔다.

## 49.9 incident 대응

incident 중:

- 사용자 영향과 범위
- commander와 역할
- 변경 동결
- 완화 우선
- timestamped action log
- 외부 communication
- 증거 보존

사후:

```text
무슨 일이 있었는가
영향
timeline
근본 원인과 기여 요인
탐지가 늦은 이유
잘 작동한 것
개선 action + owner + deadline
```

개인의 실수에서 멈추지 않는다. 왜 한 번의 실수가 production 전체에 도달했는지 시스템 조건을 찾는다.

## 49.10 SLI, SLO, error budget

SLI는 측정, SLO는 목표다.

```text
SLI: 성공한 match create 비율
SLO: 30일 rolling 99.95%
```

error budget은 허용 실패량이다. 안정성 목표를 제품 속도와 연결한다.

잘못된 SLI는 내부 component가 정상이어도 사용자 실패를 놓친다. 사용자 관점의 end-to-end 지표를 포함한다.

## 49.11 안전과 윤리

프로그래머의 판단은 사람에게 영향을 준다.

질문:

- 어떤 데이터가 정말 필요한가?
- 사용자가 동의하고 삭제할 수 있는가?
- 접근성은 고려했는가?
- 확률 시스템과 과금이 취약 사용자를 악용하는가?
- 자동화 오류의 이의 제기 경로가 있는가?
- 모델의 편향과 오판 비용은 누구에게 가는가?
- 보안 결함을 발견했을 때 책임 있는 공개 절차가 있는가?

법 준수는 최소선이다. 만들 수 있다는 사실과 만들어야 한다는 판단은 다르다.

<div class="lab">

### 최종 실습: StoneKV 복구 시험

1. 1,000개 random operation 생성
2. 각 write byte 위치에서 process kill
3. restart와 recovery
4. committed prefix와 state 비교
5. disk full, permission change, checksum corruption 주입
6. RPO/RTO 측정
7. operator runbook 작성
8. postmortem 형식으로 발견된 결함 기록

</div>

<div class="check">

### 제9부 통과 기준

- 시스템의 자산·공격자·신뢰 경계를 그림으로 표현한다.
- 최소 권한과 fail-safe default를 실제 API에 적용한다.
- 비신뢰 parser에 크기·깊이·시간 제한을 둔다.
- memory sanitizer와 fuzzing을 CI에 결합한다.
- dependency lock, SBOM, signed artifact 흐름을 설명한다.
- overload에서 bounded queue와 load shedding을 실험한다.
- backup restore와 장애 주입을 자동화한다.
- incident postmortem을 개인 비난 없이 시스템 개선으로 연결한다.

</div>
