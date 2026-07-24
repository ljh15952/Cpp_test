# Aster DX12 Companion Code

이 코드는 《DirectX 12 게임 엔진과 실시간 그래픽스》의 실습 부록이다.

## 포함 내용

- portable C++20 core
  - vector/matrix math와 reversed-Z projection
  - generation handle pool
  - linear arena
  - 최소 render graph dependency compiler
  - 작은 thread-pool job system
  - CPU GGX BRDF reference
- Windows 전용 D3D12 triangle
  - debug layer
  - adapter/device/queue/fence/swap chain
  - root signature/PSO
  - resize와 frames-in-flight
- HLSL examples
  - triangle
  - PBR
  - tone mapping
  - TAA skeleton
  - clustered-light list skeleton

## 빌드

### Portable tests

```bash
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
```

### Windows D3D12 sample

Visual Studio 2022 Developer PowerShell 또는 CMake/Ninja 환경에서 같은 명령을 실행한다. Windows SDK의 `d3d12`, `dxgi`, `d3dcompiler`가 필요하다.

D3D12 sample은 교육용 최소 코드다. production 엔진에서는 DXC/Shader Model 6, Agility SDK, render graph, descriptor allocator, DRED report를 책의 단계에 따라 추가한다.

## 검증 범위

portable core는 GCC/Clang/MSVC에서 컴파일할 수 있도록 작성했다. 배포 패키지 제작 시 Linux 환경에서 portable tests를 실행했다. Windows 전용 D3D12 executable은 Windows SDK가 없는 제작 환경에서는 실제 컴파일하지 못했으므로, Windows에서 직접 빌드하고 debug layer 메시지 0을 확인해야 한다.
