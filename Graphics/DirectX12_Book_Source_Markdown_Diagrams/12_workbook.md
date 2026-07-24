# 117. 연습문제 워크북

이 워크북은 답을 읽기 전에 직접 구현하는 용도다. 문제마다 다음 표기를 사용한다.

- **[개념]** 종이에 식과 그림으로 설명
- **[코드]** 컴파일 가능한 최소 구현
- **[실험]** PIX/수치/이미지로 비교
- **[설계]** API, 수명, 실패 모드 제시
- **[논문]** 원문을 읽고 가정과 구현 차이를 정리

## A. 수학과 좌표계 1–20

1. **[개념]** dot product를 projection과 cosine 두 관점으로 유도한다.
2. **[코드]** zero vector를 안전하게 처리하는 `Normalize`를 작성한다.
3. **[개념]** cross product의 방향과 면적 의미를 설명한다.
4. **[코드]** 세 점으로 triangle area와 winding을 구한다.
5. **[코드]** Gram–Schmidt로 orthonormal basis를 만든다.
6. **[개념]** point와 direction에 homogeneous `w`가 각각 1과 0인 이유를 설명한다.
7. **[코드]** TRS compose/decompose를 구현하고 실패 조건을 적는다.
8. **[개념]** matrix multiplication order가 변환 순서를 바꾸는 예를 만든다.
9. **[코드]** look-at view matrix를 직접 구현한다.
10. **[코드]** perspective projection의 각 항을 near/far/FOV/aspect에서 유도한다.
11. **[개념]** clip space와 NDC를 구분한다.
12. **[실험]** standard-Z와 reversed-Z depth quantization을 그래프로 비교한다.
13. **[코드]** quaternion axis-angle, multiplication, rotate-vector를 구현한다.
14. **[개념]** quaternion double cover와 shortest-path slerp를 설명한다.
15. **[코드]** screen pixel에서 world ray를 복원한다.
16. **[개념]** radiance와 irradiance의 단위 차이를 설명한다.
17. **[코드]** linear↔sRGB conversion을 구현하고 round-trip error를 측정한다.
18. **[개념]** Nyquist 관점에서 texture aliasing을 설명한다.
19. **[코드]** Hammersley sequence와 cosine hemisphere sampling을 구현한다.
20. **[실험]** uniform/importance sampling estimator variance를 비교한다.

## B. D3D12 기초 21–45

21. **[개념]** device, queue, allocator, command list의 역할을 구분한다.
22. **[코드]** adapter를 열거하고 dedicated memory와 feature level을 출력한다.
23. **[코드]** debug layer와 DRED를 device 생성 전에 활성화한다.
24. **[개념]** command allocator를 fence 전에 reset하면 안 되는 이유를 timeline으로 그린다.
25. **[코드]** graphics queue와 fence를 감싼 `GpuTimeline`을 작성한다.
26. **[코드]** flip-model swap chain과 resize를 구현한다.
27. **[실험]** buffer count 2와 3의 latency/throughput을 비교한다.
28. **[개념]** committed/placed/reserved resource를 비교한다.
29. **[코드]** upload buffer suballocator를 256-byte alignment와 함께 구현한다.
30. **[코드]** texture upload footprint를 `GetCopyableFootprints`로 계산한다.
31. **[개념]** RTV/DSV/CBV/SRV/UAV와 descriptor heap visibility를 설명한다.
32. **[코드]** CPU descriptor free-list allocator를 구현한다.
33. **[코드]** shader-visible descriptor ring을 frames-in-flight와 연동한다.
34. **[개념]** descriptor lifetime과 resource lifetime이 다른 예를 든다.
35. **[코드]** legacy resource state tracker를 구현한다.
36. **[설계]** enhanced barrier intent를 엔진 access enum으로 추상화한다.
37. **[코드]** DXC로 HLSL을 compile하고 include/error를 출력한다.
38. **[코드]** root signature serialize/validation helper를 작성한다.
39. **[실험]** root constant, root CBV, descriptor table의 CPU/GPU 비용을 비교한다.
40. **[코드]** graphics PSO key와 hash를 구현한다.
41. **[설계]** shader permutation explosion을 줄이는 정책을 만든다.
42. **[코드]** indexed cube와 texture를 upload해 그린다.
43. **[실험]** debug layer 경고를 의도적으로 5개 만들고 고친다.
44. **[코드]** GPU object deferred destruction queue를 구현한다.
45. **[실험]** device removed를 장시간 shader로 재현하지 말고, 안전한 mock/log test로 DRED report path를 검증한다.

## C. 렌더러 아키텍처 46–65

46. **[설계]** World→RenderExtraction→Renderer→D3D12 의존 그래프를 만든다.
47. **[코드]** `FrameContext`에 allocator/upload/descriptors/retired object를 묶는다.
48. **[설계]** 두 queue가 resource를 공유할 때 retirement condition을 정의한다.
49. **[코드]** pass/resource handle 기반 최소 render graph API를 만든다.
50. **[코드]** last-writer/readers로 dependency edge를 생성한다.
51. **[코드]** topological sort와 cycle diagnostics를 구현한다.
52. **[코드]** unused pass culling을 구현한다.
53. **[코드]** resource first/last use를 계산한다.
54. **[설계]** transient aliasing allocator를 interval coloring 문제로 설명한다.
55. **[코드]** render graph를 DOT 파일로 출력한다.
56. **[코드]** frustum plane extraction과 sphere/AABB test를 구현한다.
57. **[실험]** front-to-back sorting이 early-Z에 미치는 효과를 측정한다.
58. **[코드]** stable draw key를 만들고 radix sort한다.
59. **[코드]** 4 worker command recording을 구현한다.
60. **[실험]** command list 개수와 CPU record/submission 비용을 비교한다.
61. **[설계]** persistent GPU scene의 stable index와 dirty update를 설계한다.
62. **[코드]** compute frustum culling과 visible append를 구현한다.
63. **[코드]** ExecuteIndirect draw path를 구현한다.
64. **[실험]** CPU draw와 indirect draw의 crossover point를 찾는다.
65. **[논문]** FrameGraph 발표의 resource lifetime idea를 자신의 graph compiler와 비교한다.

## D. PBR과 재료 66–90

66. **[개념]** rendering equation 각 항을 자신의 말로 설명한다.
67. **[코드]** Lambert BRDF를 `1/π` 포함해 구현한다.
68. **[코드]** GGX NDF를 구현하고 roughness별 그래프를 그린다.
69. **[코드]** Schlick Fresnel과 exact dielectric Fresnel을 비교한다.
70. **[코드]** correlated Smith visibility를 구현한다.
71. **[코드]** metallic/roughness BRDF를 조립한다.
72. **[실험]** white furnace test를 자동화한다.
73. **[실험]** roughness 0/1, NoV≈0, black/white material의 NaN을 검사한다.
74. **[개념]** dielectric과 conductor의 base color 의미를 설명한다.
75. **[코드]** tangent basis와 mirrored UV handedness를 처리한다.
76. **[코드]** inverse-transpose normal transform을 구현한다.
77. **[실험]** normal map의 sRGB 설정 오류를 캡처한다.
78. **[코드]** specular anti-aliasing roughness 보정을 구현한다.
79. **[코드]** cubemap diffuse convolution을 구현한다.
80. **[코드]** SH9 projection/evaluation을 구현한다.
81. **[코드]** GGX environment prefilter를 compute shader로 구현한다.
82. **[코드]** BRDF integration LUT를 생성한다.
83. **[실험]** split-sum IBL을 path-traced reference와 비교한다.
84. **[코드]** parallax-corrected box probe를 구현한다.
85. **[설계]** reflection probe blending/priority 구조를 만든다.
86. **[코드]** material GPU struct와 bindless indices를 구현한다.
87. **[설계]** BC format을 material texture semantic별로 선택한다.
88. **[논문]** Disney BRDF parameter가 UE4 모델에서 어떻게 단순화됐는지 표로 만든다.
89. **[논문]** Cook–Torrance와 현대 GGX 구현의 차이를 정리한다.
90. **[선택]** LTC rectangular area light를 구현한다.

## E. Lighting, Shadow, Post 91–120

91. **[설계]** Forward+, Deferred, hybrid 중 하나를 요구사항으로 선택한다.
92. **[코드]** logarithmic cluster z slicing을 구현한다.
93. **[코드]** sphere-cluster intersection을 구현한다.
94. **[코드]** count/scan/fill light list를 구현한다.
95. **[실험]** cluster size와 light list 길이/GPU 시간을 비교한다.
96. **[코드]** inverse-square point light와 smooth cutoff를 구현한다.
97. **[코드]** shadow map과 comparison sampler를 구현한다.
98. **[실험]** constant/slope/normal bias를 canonical scene에서 비교한다.
99. **[코드]** 3×3, 5×5 PCF를 구현한다.
100. **[코드]** practical cascade split을 구현한다.
101. **[코드]** shadow texel snapping으로 CSM을 안정화한다.
102. **[실험]** cascade resolution과 visible shimmering을 측정한다.
103. **[코드]** VSM을 구현하고 light bleeding scene을 만든다.
104. **[코드]** half-resolution GTAO와 bilateral upsample을 구현한다.
105. **[코드]** Hi-Z pyramid를 구현한다.
106. **[코드]** 간단한 SSR과 confidence fallback을 구현한다.
107. **[코드]** exponential height fog를 구현한다.
108. **[선택]** froxel volumetric을 구현한다.
109. **[코드]** luminance histogram auto exposure를 구현한다.
110. **[코드]** Reinhard와 filmic curve를 비교한다.
111. **[실험]** channel-wise/luminance-wise tone map의 hue 차이를 비교한다.
112. **[코드]** Halton jitter와 motion vector를 구현한다.
113. **[코드]** TAA reprojection과 depth rejection을 구현한다.
114. **[코드]** neighborhood variance clipping을 구현한다.
115. **[실험]** camera cut, emissive, transparency ghosting scene을 만든다.
116. **[코드]** dynamic resolution controller를 구현한다.
117. **[코드]** bloom pyramid를 구현한다.
118. **[코드]** premultiplied alpha pipeline을 구현한다.
119. **[선택]** weighted blended OIT를 구현한다.
120. **[실험]** 최종 post stack의 pass별 GPU 비용과 history memory를 표로 만든다.

## F. 엔진 시스템 121–145

121. **[코드]** generation handle pool과 stale handle test를 구현한다.
122. **[코드]** sparse set add/get/remove를 구현한다.
123. **[실험]** AoS, SoA, sparse set iteration을 비교한다.
124. **[코드]** transform hierarchy와 cycle detection을 구현한다.
125. **[코드]** fixed timestep과 interpolation을 구현한다.
126. **[설계]** gameplay/animation/physics/transform phase DAG를 만든다.
127. **[코드]** work-stealing job system 최소 버전을 구현한다.
128. **[코드]** job counter의 help-waiting을 구현한다.
129. **[실험]** grain size와 worker 수를 바꿔 scaling을 측정한다.
130. **[코드]** AssetId, content hash, dependency graph를 구현한다.
131. **[코드]** versioned runtime asset header를 구현한다.
132. **[코드]** texture async loading state machine을 구현한다.
133. **[설계]** cancel, failure, fallback, retry 정책을 만든다.
134. **[코드]** shader include dependency와 hot reload를 구현한다.
135. **[코드]** GPU resource two-phase publication과 retirement를 구현한다.
136. **[코드]** skeleton hierarchy와 linear blend skinning을 구현한다.
137. **[코드]** previous bone palette로 motion vector를 구현한다.
138. **[선택]** dual quaternion skinning을 구현한다.
139. **[코드]** animation clip player와 blend node를 구현한다.
140. **[설계]** editor scene/runtime save/network snapshot을 구분한다.
141. **[코드]** schema migration test를 구현한다.
142. **[코드]** command-based undo/redo를 구현한다.
143. **[코드]** render extraction snapshot을 구현한다.
144. **[실험]** snapshot copy와 direct shared-world 접근의 비용/race를 비교한다.
145. **[선택]** DirectStorage sample을 자신의 asset package에 연결한다.

## G. 고급 GPU·DXR 146–170

146. **[코드]** group shared reduction을 구현한다.
147. **[코드]** wave intrinsic reduction을 구현하고 비교한다.
148. **[코드]** hierarchical exclusive scan을 구현한다.
149. **[코드]** stream compaction을 구현한다.
150. **[코드]** 32-bit radix sort를 구현한다.
151. **[실험]** async compute 후보 pass 3개를 비교한다.
152. **[코드]** meshlet builder를 구현한다.
153. **[코드]** normal cone culling을 구현한다.
154. **[선택]** amplification/mesh shader path를 구현한다.
155. **[선택]** VRS shading-rate image를 구현한다.
156. **[선택]** sampler feedback 요청을 시각화한다.
157. **[설계]** Work Graphs와 ExecuteIndirect의 적용 범위를 비교한다.
158. **[코드]** BLAS/TLAS build helper를 구현한다.
159. **[코드]** inline ray-traced hard shadow를 구현한다.
160. **[코드]** ray-traced reflection과 probe fallback을 구현한다.
161. **[코드]** temporal ray denoise history validation을 구현한다.
162. **[코드]** luminance moments와 variance를 구현한다.
163. **[코드]** A-trous edge-aware filter를 구현한다.
164. **[논문]** SVGF의 각 pass를 자신의 구현과 대응시킨다.
165. **[코드]** weighted reservoir update를 구현한다.
166. **[논문]** ReSTIR DI의 proposal/target PDF와 normalization을 정리한다.
167. **[코드]** CPU 또는 DXR reference path tracer를 구현한다.
168. **[코드]** Russian roulette와 MIS를 구현한다.
169. **[실험]** raster PBR, hybrid reflection, path-traced reference를 비교한다.
170. **[설계]** 지원하지 않는 GPU의 fallback feature matrix를 만든다.

## H. 디버깅·성능·면접 171–200

171. **[코드]** CPU scope profiler와 percentile 통계를 구현한다.
172. **[코드]** GPU timestamp query profiler를 구현한다.
173. **[코드]** render graph pass 이름으로 PIX event를 자동 생성한다.
174. **[코드]** resource lifetime log를 구현한다.
175. **[코드]** DRED report를 JSON/text로 저장한다.
176. **[실험]** 해상도/object/light 수 scaling matrix를 만든다.
177. **[실험]** 3개 G-buffer layout을 비교한다.
178. **[실험]** overdraw view와 depth prepass 효과를 비교한다.
179. **[실험]** draw call 1/1k/100k benchmark를 만든다.
180. **[실험]** root parameter/descriptor update 전략을 비교한다.
181. **[코드]** shader NaN/Inf detector와 first-failure capture를 구현한다.
182. **[코드]** golden image diff tool을 구현한다.
183. **[코드]** renderer snapshot replay를 구현한다.
184. **[실험]** 성능 개선 하나를 A/B capture로 검증한다.
185. **[문서]** 실패한 최적화 한 개를 원인과 함께 기록한다.
186. **[면접]** D3D11과 D3D12의 책임 차이를 설명한다.
187. **[면접]** fence와 barrier의 차이를 설명한다.
188. **[면접]** UAV barrier가 필요한 예를 든다.
189. **[면접]** bindless의 장점과 위험을 설명한다.
190. **[면접]** render graph의 compile 단계 7개를 설명한다.
191. **[면접]** PBR white furnace 실패 원인을 3개 제시한다.
192. **[면접]** shadow shimmering을 조사하는 순서를 말한다.
193. **[면접]** TAA ghosting을 data 관점에서 분해한다.
194. **[면접]** GPU-driven 전환의 crossover를 어떻게 찾는지 설명한다.
195. **[면접]** sparse set과 archetype ECS를 비교한다.
196. **[면접]** async asset upload의 수명과 fence를 설명한다.
197. **[면접]** PIX에서 pixel-bound를 증명하는 실험을 제시한다.
198. **[면접]** DXR BLAS/TLAS update 정책을 설명한다.
199. **[면접]** 논문을 production 기능으로 옮길 때 확인할 항목을 말한다.
200. **[면접]** 자신의 최종 프로젝트에서 가장 어려운 tradeoff를 수치로 설명한다.

# 118. 20개 미니 프로젝트

1. CPU ray caster와 camera math
2. D3D12 triangle + robust resize
3. Upload/descriptor playground
4. Texture viewer + mip/color-space debug
5. PBR material sphere grid
6. IBL baker
7. Clustered light stress test
8. Shadow bias laboratory
9. TAA ghosting laboratory
10. Render graph visualizer
11. Multithreaded command recorder benchmark
12. Generation handle ECS sandbox
13. Asset cooker + hot reload
14. Skeletal animation viewer
15. GPU culling + indirect demo
16. Meshlet viewer
17. Ray-traced shadow + denoise
18. Reference path tracer
19. PIX performance laboratory
20. Aster Engine capstone

각 미니 프로젝트는 `README`, 실행 영상, 실패 사례, 수치표를 포함한다.
