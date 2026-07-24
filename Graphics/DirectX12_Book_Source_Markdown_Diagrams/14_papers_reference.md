# 121. 논문 읽기 로드맵

그래픽스 논문은 처음부터 모든 수식을 완벽히 이해하려고 하면 진행이 멈춘다. 다음 순서로 읽는다.

1. **문제:** 기존 방법의 어떤 실패를 해결하는가?
2. **가정:** static scene, one bounce, isotropic BRDF, screen-space 등 무엇을 제한하는가?
3. **Estimator/Model:** 어떤 양을 계산하는가?
4. **입력 데이터:** depth, normal, motion, samples, PDFs는 무엇인가?
5. **비용:** sample 수, pass 수, memory, synchronization은?
6. **오차:** bias, variance, artifact, failure case는?
7. **Production adaptation:** 논문과 엔진 구현의 차이는?
8. **검증:** reference와 어떤 metric으로 비교했는가?

## 121.1 1단계: 고전 조명과 빛 수송

### Phong 1975 / Blinn 1977

읽을 질문:

- empirical highlight는 어떤 시각적 요구를 해결했는가?
- exponent가 highlight 모양을 어떻게 바꾸는가?
- 왜 물리 기반 workflow로는 부족한가?

참고: [@phong1975; @blinn1977].

### Cook–Torrance 1981

- microfacet distribution, Fresnel, geometry attenuation의 역할
- roughness와 wavelength/reflectance의 관계
- 현대 GGX와 어떤 부분이 다른가?

참고: [@cook1981].

### Kajiya 1986

- rendering equation의 fixed-point 형태
- path가 어떻게 light transport를 표현하는가?
- Monte Carlo estimator와 어떻게 연결되는가?

참고: [@kajiya1986].

## 121.2 2단계: 현대 PBR

### Walter et al. 2007

- microfacet reflection/refraction의 unified form
- GGX/Trowbridge–Reitz distribution
- half-vector Jacobian과 PDF

참고: [@walter2007].

### Heitz 2014

- masking-shadowing function을 왜 이해해야 하는가?
- visible normal distribution은 sampling variance를 어떻게 줄이는가?

참고: [@heitz2014].

### Disney 2012 / UE4 2013 / Frostbite 2014

세 자료를 비교한다.

| 질문 | Disney | UE4 | Frostbite |
|---|---|---|---|
| 주된 목표 | artist-friendly principled model | 실시간 게임 표준화 | 물리 단위부터 제작 파이프라인 |
| diffuse/specular | 다양한 lobe | 단순화된 기본 model | production calibration |
| IBL | 원리/재료 중심 | split-sum 구현 | probe/exposure/lighting workflow |

참고: [@burley2012; @karis2013; @lagarde2014].

## 121.3 3단계: 많은 빛과 그림자

### Forward+ / Clustered Shading

- 2D tile의 depth worst case
- cluster grid와 light assignment
- memory list overflow
- opaque/transparent 공유

참고: [@harada2012; @olsson2012].

### Shadow Map / PCF / VSM

- visibility를 depth map으로 근사하는 핵심
- comparison 결과 filtering과 depth moment filtering의 차이
- bias와 light bleeding이라는 서로 다른 artifact

참고: [@williams1978; @reeves1987; @donnelly2006].

## 121.4 4단계: 시간적 재구성

### Temporal Supersampling

- jitter가 sample pattern을 어떻게 확장하는가?
- reprojection이 실패하는 조건
- neighborhood clamp가 bias/ghosting을 어떻게 바꾸는가?

참고: [@karis2014taa].

### SMAA

- edge detection/search/blend weight 계산
- spatial morphology와 temporal method의 역할 차이

참고: [@jimenez2012smaa].

## 121.5 5단계: 화면 공간 효과

### GTAO

- horizon integration
- screen-space에서 ground truth를 근사한다는 의미
- temporal/spatial denoise와 failure cases

참고: [@jimenez2016gtao].

### Weighted Blended OIT

- order-independent가 아니라 order-independent approximation인 이유
- weight function이 결과에 미치는 영향

참고: [@mcguire2013oit].

## 121.6 6단계: GPU 엔진 구조

### FrameGraph

- pass/resource dependency
- transient lifetime
- production feature modularity

참고: [@odonnell2017].

### GPU BVH Construction

- Morton code, radix tree, parallel hierarchy construction
- build quality와 build speed tradeoff

참고: [@karras2012].

### Ray Traversal

- SIMD divergence와 ray coherence
- node/triangle intersection throughput

참고: [@aila2009].

## 121.7 7단계: 실시간 Ray Tracing

### SVGF

- temporal moments와 variance
- edge-aware A-trous filter
- disocclusion handling

참고: [@schied2017].

### ReSTIR DI

- reservoir sampling
- temporal/spatial reuse
- target/proposal distribution
- bias와 visibility reuse

참고: [@bitterli2020].

## 121.8 논문 재현 보고서 템플릿

```text
논문:
해결 문제:
원 논문의 가정:
내 엔진의 제약:
구현한 식/알고리즘:
생략한 부분:
변경한 부분과 이유:
reference 구현/이미지:
테스트 장면:
품질 결과:
성능 결과:
실패 사례:
다음 개선:
```

# 122. DirectX 12 공식 문서 읽기 순서

공식 문서는 API reference만 검색해서 읽지 말고 개념→샘플→사양 순으로 본다.

1. D3D12 programming guide [@microsoft-d3d12-guide]
2. DirectX Graphics Samples의 HelloWorld/MiniEngine [@microsoft-d3d12-samples]
3. root signatures와 resource binding [@microsoft-root-signatures; @microsoft-resource-binding]
4. memory management/residency [@microsoft-memory-management; @microsoft-residency]
5. HLSL/DXC [@microsoft-hlsl; @microsoft-dxc]
6. PIX GPU/timing capture [@microsoft-pix-gpu; @microsoft-pix-timing]
7. Enhanced Barriers [@microsoft-enhanced-barriers]
8. Mesh Shader, DXR, VRS, Sampler Feedback [@microsoft-mesh-shader; @microsoft-dxr; @microsoft-vrs; @microsoft-sampler-feedback]
9. Work Graphs [@microsoft-work-graphs]
10. DirectStorage [@microsoft-directstorage]

샘플 코드는 동작 확인용이지 그대로 엔진 architecture로 복사할 설계 정답이 아니다. 샘플의 목표와 생략된 failure path를 확인한다.

# 123. 수식 Quick Reference

## 123.1 Vector

$$a\cdot b=|a||b|\cos\theta$$

$$|a\times b|=|a||b|\sin\theta$$

Reflection:

$$r=i-2(n\cdot i)n$$

## 123.2 Transform

열벡터 표기:

$$p_{clip}=PVMp_{local}$$

Normal:

$$n'=\mathrm{normalize}((M^{-1})^T n)$$

## 123.3 Perspective divide

$$p_{ndc}=p_{clip}/w_{clip}$$

## 123.4 Rendering equation

$$L_o=L_e+\int_{\Omega^+}f_rL_i(n\cdot\omega_i)d\omega_i$$

## 123.5 Monte Carlo

$$I\approx\frac1N\sum_i\frac{f(X_i)}{p(X_i)}$$

## 123.6 Microfacet

$$f_s=\frac{DFG}{4NoLNoV}$$

Schlick:

$$F=F_0+(1-F_0)(1-VoH)^5$$

## 123.7 Inverse-square light

$$E=I/r^2$$

## 123.8 Alpha blend

Straight alpha:

$$C_o=C_s\alpha_s+C_d(1-\alpha_s)$$

Premultiplied:

$$C_o=C_s+C_d(1-\alpha_s)$$

## 123.9 Percentile budget

60fps:

$$1000/60\approx16.67\text{ ms}$$

# 124. D3D12 Quick Reference

## 124.1 프레임 순서

```text
wait/reuse FrameContext
→ reset allocator/list
→ acquire back buffer index
→ record upload/barriers/passes
→ close/execute
→ present
→ signal fence
→ store fence in FrameContext
```

## 124.2 Resource upload

```text
default resource(COPY_DEST)
+ upload resource(GENERIC_READ)
→ CopyBufferRegion/CopyTextureRegion
→ transition to final access
→ keep upload alive until copy fence
```

## 124.3 Descriptor

- RTV/DSV: CPU-only heap
- CBV/SRV/UAV, Sampler: shader-visible 가능
- handle increment는 heap type별 device query
- descriptor slot 재사용도 fence를 고려

## 124.4 Queue synchronization

```text
copy queue uploads → signal copy fence C
graphics queue Wait(C)
→ consume resource
→ signal graphics fence G
CPU/resource manager retires at completed G
```

## 124.5 Debug checklist

- debug layer enabled before device
- object names
- PIX markers
- HRESULT checked
- fence values logged
- resource states asserted
- descriptor capacity checked
- DRED enabled

# 125. HLSL Quick Reference

## 125.1 Constant buffer alignment

C++ layout과 HLSL packing을 static assertion/reflection으로 검증한다.

```hlsl
cbuffer ViewConstants : register(b0)
{
    float4x4 ViewProjection;
    float4x4 PreviousViewProjection;
    float3 CameraPosition;
    float Exposure;
};
```

## 125.2 Common semantics

```text
SV_Position
SV_VertexID / SV_InstanceID
SV_Target0...
SV_Depth
SV_DispatchThreadID
SV_GroupID / SV_GroupThreadID / SV_GroupIndex
```

## 125.3 Derivatives

`ddx`, `ddy`, `fwidth`는 pixel quad에서 정의된다. divergent control flow 안에서 derivative 결과가 불안정할 수 있다.

## 125.4 Barriers

```hlsl
GroupMemoryBarrierWithGroupSync();
DeviceMemoryBarrier();
AllMemoryBarrierWithGroupSync();
```

shader barrier와 D3D12 resource barrier는 다른 계층이다. group barrier는 dispatch 간 순서를 만들지 않는다.

# 126. 용어집

| 용어 | 정의 |
|---|---|
| BRDF | 입사 방향의 irradiance가 출력 방향 radiance로 분배되는 함수 |
| BSDF | 반사와 투과를 포함한 scattering 함수 |
| NDF | microfacet normal의 통계 분포 |
| Fresnel | 입사각과 굴절률에 따른 반사율 |
| Radiance | 방향을 가진 빛의 운반량 |
| Irradiance | 표면에 입사하는 radiance의 cosine 적분 |
| Descriptor | GPU resource view를 설명하는 작은 record |
| PSO | shader와 fixed-function state의 pipeline 객체 |
| Fence | queue/CPU 실행 완료 시점 동기화 값 |
| Barrier | resource access/layout/state 사이의 순서·가시성 전환 |
| Residency | resource memory가 GPU 접근 가능한 상태 |
| Render Graph | pass와 resource dependency를 선언·compile하는 구조 |
| Bindless | shader가 index를 통해 큰 resource descriptor 집합에 접근하는 방식 |
| Meshlet | GPU culling/mesh shader에 적합한 작은 mesh cluster |
| TAA | 여러 frame의 jittered sample을 재투영·누적하는 anti-aliasing |
| Denoising | noisy estimator를 temporal/spatial 정보로 복원하는 과정 |
| BLAS/TLAS | DXR geometry/instance acceleration structure 계층 |
| Reservoir | weighted stream에서 sample과 누적 통계를 유지하는 구조 |
| DRED | D3D12 device removal의 breadcrumb/page-fault 진단 기능 |

# 127. 마지막 학습 규칙

1. 식을 보면 코드로 쓴다.
2. 코드를 보면 실패 case를 만든다.
3. 화면을 보면 수치를 캡처한다.
4. 최적화하면 품질과 복잡성의 부작용을 적는다.
5. 논문을 인용하면 원래 가정과 자신의 변경을 적는다.
6. 최신 기능은 feature query와 fallback을 함께 구현한다.
7. 자신의 코드를 일본어로 설명할 수 있을 때까지 반복한다.

이 규칙을 지키면 “DirectX API를 조금 아는 사람”에서 “엔진과 그래픽스 문제를 정의·구현·측정하는 사람”으로 이동한다.
