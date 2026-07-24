# C++ Game Client Book — Companion Code

이 코드는 전자책의 핵심 실습을 독립적으로 빌드하기 위한 C++20 예제입니다.

## Build

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
```

## Contents

- `health.hpp`: 불변식을 가진 값 타입
- `handle_pool.hpp`: generation 기반 안전 핸들
- `fixed_stepper.hpp`: 고정 시간 스텝 누산기
- `state_machine.hpp`: Dead/Dodge/Stun 규칙이 있는 상태 머신
- `math.hpp`: Vector3, dot, cross, normalize
- `statistics.hpp`: 평균과 percentile
- `unsafe_demos/`: Sanitizer 학습용 의도적 오류. 기본 빌드에서는 제외됩니다.

## Sanitizer example (GCC/Clang)

```bash
cmake -S . -B build-asan \
  -DCPPBOOK_BUILD_UNSAFE_DEMOS=ON \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer"
cmake --build build-asan
./build-asan/use_after_free_demo
```

의도적 오류 프로그램은 학습 전용입니다.
https://chatgpt.com/share/e/6a6322aa-5214-83ee-a2ea-5de37c5ac7dd
