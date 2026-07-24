# Apex Foundations — C++20 동반 코드

전자책 **《컴퓨터를 끝까지 이해하는 프로그래머》**의 실행 가능한 최소 구현이다.

## 포함 내용

- `Bits.hpp`: 8-bit ALU flag와 endian
- `Tiny8`: 8-bit CPU emulator, CALL/RET, trace
- `Expression`: lexer, recursive-descent compiler, stack VM
- `HandlePool`: generation handle과 stale reference 검출
- `LinearArena`: alignment를 처리하는 frame-style arena
- `Graph`: deterministic topological sort와 cycle 진단
- `GameLoop`: fixed timestep accumulator와 overload policy
- `WalKv`: 명시적 binary encoding, checksum, partial-tail recovery

## 빌드

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/apex_labs
```

Sanitizer:

```bash
cmake -S . -B build-asan \
  -DCMAKE_BUILD_TYPE=Debug \
  -DAPEX_ENABLE_SANITIZERS=ON
cmake --build build-asan -j
ctest --test-dir build-asan --output-on-failure
```

## 의도적 제한

이 코드는 production engine이나 database가 아니다.

- `LinearArena`는 trivially destructible type만 허용한다.
- `WalKv::flush`는 C++ stream flush이며 모든 OS에서 stable storage `fsync`를 보장하지 않는다.
- checksum은 accidental corruption 탐지이고 공격자에 대한 cryptographic MAC이 아니다.
- Tiny-8은 실제 ISA timing, interrupt, protection을 생략한다.
- expression 언어는 variable, closure, GC 전 단계의 학습용 subset이다.

책의 연습문제에 따라 사양, failure injection, fuzzing, benchmark를 확장한다.
