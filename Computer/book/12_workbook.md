# 부록 A — 280개 연습문제 워크북


이 문제는 정답 암기보다 **설명·구현·반례·측정·장애 주입**을 요구한다. 각 문제에 다음 증거 중 적어도 하나를 남긴다.


- 실행 가능한 코드와 test
- diagram과 invariant
- profiler/trace/sanitizer 결과
- 논문 카드와 출처
- 실험 환경·raw data·결론
- 실패를 재현하는 최소 입력


난이도 표시는 의도적으로 넣지 않았다. 자신이 자료 없이 완성할 수 있는지를 기준으로 지식 등급을 기록한다.


# 제1부 — 역사와 계산


1. [설명] 주판, 기계식 계산기, 저장 프로그램 컴퓨터의 차이를 ‘명령 표현’ 관점에서 비교하라.

2. [연표] Babbage, Boole, Turing, Shannon, von Neumann, transistor, integrated circuit, microprocessor를 하나의 인과 연표로 연결하라.

3. [논증] Turing machine이 실제 컴퓨터의 정확한 회로 설계도가 아닌데도 중요한 이유를 설명하라.

4. [반례] ‘컴퓨터는 숫자만 계산한다’는 주장에 반례 세 개를 들고, 결국 bit pattern으로 귀결되는 과정을 쓰라.

5. [설명] universal machine 개념과 프로그램을 데이터로 취급하는 생각의 관계를 설명하라.

6. [비교] Harvard architecture와 von Neumann architecture의 장단점을 코드/데이터 경로 관점에서 비교하라.

7. [조사] ENIAC의 초기 프로그래밍 방식과 stored-program 방식의 변경 비용을 비교하는 1쪽 보고서를 작성하라.

8. [설명] transistor가 vacuum tube보다 시스템 규모 확장에 유리했던 이유를 전력·신뢰성·크기 관점에서 설명하라.

9. [논문] Turing 1936 논문의 핵심 문제, machine model, 한계를 논문 카드 형식으로 정리하라.

10. [논문] von Neumann EDVAC 보고서가 프로그램 저장과 제어에 미친 영향을 원문 근거로 요약하라.

11. [설명] Moore의 법칙을 자연 법칙이 아니라 산업 관찰·목표로 해석해야 하는 이유를 쓰라.

12. [사고실험] 메모리와 CPU 속도가 같다면 현재 software architecture 중 무엇이 달라질지 세 가지 예측하라.

13. [사고실험] 네트워크 latency가 0이어도 분산 시스템의 모든 문제가 사라지지 않는 이유를 설명하라.

14. [비교] batch processing, time sharing, personal computing, cloud computing이 최적화한 자원을 비교하라.

15. [설명] Unix의 process, file, pipe 추상화가 composition에 준 영향을 작은 shell pipeline으로 보이라.

16. [조사] C, C++, Java, Python, Rust의 등장 배경에서 각각 해결하려던 제약을 표로 비교하라.

17. [논증] 새로운 언어가 이전 언어를 완전히 대체하지 못하는 이유를 기술·경제·생태계 관점에서 쓰라.

18. [설명] ARPANET과 end-to-end argument가 현대 인터넷 구조에 준 영향을 연결하라.

19. [조사] relational database 이전의 data model과 Codd 모델의 차이를 application coupling 관점에서 정리하라.

20. [설명] open source가 단순 무료 배포와 다른 점을 collaboration, auditability, governance 관점에서 쓰라.

21. [분석] 한 기술의 성공을 순수 기술 우수성만으로 설명할 수 없는 사례를 선택해 ecosystem과 compatibility를 분석하라.

22. [토론] ‘역사를 공부하는 것은 취업과 무관하다’는 주장에 찬반 논거를 모두 작성하라.

23. [설계] 미래의 계산 장치 하나를 상정하고, 어떤 기존 추상화가 유지되고 어떤 것이 깨질지 예측하라.

24. [설명] 계산 가능성과 계산 복잡도의 차이를 예와 함께 설명하라.

25. [증명 스케치] halting problem의 자기참조 아이디어를 코드 없이 설명하라.

26. [회고] 현재 자신이 쓰는 기술 하나를 선택해 ‘왜 등장했는가, 무엇을 숨기는가, 무엇을 못 푸는가’를 작성하라.



# 제2부 — 비트와 컴퓨터 구조


27. [계산] 8-bit unsigned와 two's complement에서 0x80, 0xFF의 값을 각각 구하라.

28. [구현] carry, signed overflow, zero, negative flag를 계산하는 8-bit add 함수를 작성하라.

29. [반례] signed overflow와 carry가 같지 않은 입력을 두 개 제시하라.

30. [설명] endian이 register 내부 bit 순서가 아니라 multi-byte memory 표현 문제인 이유를 설명하라.

31. [구현] little-endian byte sequence에서 u16/u32를 안전하게 읽는 parser를 작성하라.

32. [회로] half adder와 full adder의 truth table과 Boolean 식을 작성하라.

33. [회로] 4-bit ripple-carry adder의 critical path가 bit 수와 어떻게 늘어나는지 설명하라.

34. [설명] combinational circuit와 sequential circuit의 차이를 상태 관점에서 설명하라.

35. [설계] 두 상태 traffic light FSM을 만들고 illegal transition test를 작성하라.

36. [설명] instruction format에서 opcode bit와 operand bit 사이의 trade-off를 쓰라.

37. [구현] Tiny-8의 fetch-decode-execute 한 step을 구현하고 invalid opcode 정책을 정하라.

38. [구현] label을 지원하는 two-pass assembler를 작성하라.

39. [디버깅] stack pointer off-by-one으로 CALL/RET가 깨지는 최소 program을 만들라.

40. [설명] function call에서 calling convention과 ABI가 필요한 이유를 separate compilation과 연결하라.

41. [실험] 같은 C++ 함수를 -O0와 -O2로 compile해 assembly와 실행 시간을 비교하라.

42. [설명] pipeline hazard의 structural, data, control 종류를 예로 설명하라.

43. [실험] branch prediction이 잘 되는 loop와 안 되는 loop를 benchmark하라.

44. [설명] out-of-order CPU가 single-thread semantics를 보존하면서 명령을 재배치하는 범위를 설명하라.

45. [비교] scalar, SIMD, SIMT의 실행 모델을 비교하라.

46. [실험] array stride를 1, 2, 4, ... page size 이상으로 바꾸며 access time을 측정하라.

47. [설명] cache line과 false sharing의 관계를 thread 두 개 예로 설명하라.

48. [실험] AoS와 SoA로 particle update를 구현하고 cache miss/시간을 비교하라.

49. [설명] TLB miss가 cache miss와 다른 이유를 쓰라.

50. [설계] 2-level page table의 index와 offset을 작은 address width로 설계하라.

51. [실험] memory-mapped file과 read/write I/O의 동작 차이를 작은 프로그램으로 관찰하라.

52. [종합] C++ `vector::push_back` 한 번이 CPU, allocator, virtual memory, cache까지 거치는 비용 경로를 그리라.



# 제3부 — 운영체제와 동시성


53. [설명] process와 thread가 공유하고 공유하지 않는 자원을 표로 정리하라.

54. [실험] process 생성과 thread 생성 비용을 target OS에서 측정하라.

55. [설명] user mode와 kernel mode 전환이 필요한 system call 예를 들라.

56. [추적] 파일 한 byte를 읽을 때 library, syscall, VFS, page cache, device로 이어지는 경로를 그리라.

57. [설계] round-robin scheduler simulator를 만들고 quantum에 따른 response/throughput을 비교하라.

58. [설명] priority inversion을 세 task와 lock으로 재현하고 priority inheritance를 설명하라.

59. [구현] bounded blocking queue를 mutex와 condition variable로 구현하라.

60. [반례] condition variable을 `if`로 검사할 때 틀리는 interleaving을 쓰라.

61. [설명] data race와 race condition의 차이를 예로 설명하라.

62. [구현] atomic counter와 mutex counter를 구현하고 의미와 성능을 비교하라.

63. [설명] acquire/release가 보호하는 happens-before 관계를 message passing 예로 그리라.

64. [반례] relaxed atomic만으로 publish된 pointer의 object state가 안전하지 않은 예를 설명하라.

65. [구현] single-producer single-consumer ring buffer를 만들고 full/empty를 구분하라.

66. [검증] ThreadSanitizer로 의도적 race를 찾고 report를 해석하라.

67. [설명] deadlock의 네 조건을 dining philosophers에 대응시키라.

68. [설계] lock ordering 규칙과 debug assertion으로 deadlock을 예방하라.

69. [구현] linear arena allocator를 만들고 alignment test를 작성하라.

70. [비교] stack, heap, pool, arena allocation의 lifetime과 failure policy를 표로 작성하라.

71. [설명] reference counting cycle을 재현하고 weak reference로 해결하라.

72. [설명] tracing GC의 root, mark, sweep를 작은 object graph로 실행하라.

73. [설계] file append 중 crash를 가정하고 valid prefix를 복구하는 format을 정하라.

74. [실험] `fsync` 유무와 batch 크기에 따른 write latency를 측정하라.

75. [설명] copy-on-write fork가 page fault와 memory에 미치는 영향을 설명하라.

76. [실험] page fault 수를 sequential/random access에서 비교하라.

77. [설계] cancellation과 deadline을 가진 worker API를 설계하라.

78. [종합] 게임 main thread가 asset load를 기다려 frame hitch가 생기는 원인을 OS와 I/O 계층까지 추적하라.



# 제4부 — 언어와 컴파일러


79. [설명] lexical scope와 dynamic scope의 결과가 다른 프로그램을 작성하라.

80. [구현] integer와 identifier를 인식하는 lexer를 작성하고 source span을 보존하라.

81. [구현] 괄호와 +,*, unary -를 지원하는 recursive descent parser를 작성하라.

82. [설명] grammar의 ambiguity를 `1-2-3`과 dangling else로 설명하라.

83. [구현] parser error recovery로 한 파일에서 여러 오류를 보고하라.

84. [설계] AST를 unique_ptr tree와 arena+ID로 구현한 장단점을 비교하라.

85. [설명] name resolution과 type checking이 parsing 이후 별도 phase인 이유를 쓰라.

86. [구현] lexical environment와 nested scope lookup을 구현하라.

87. [설명] closure가 outer local의 lifetime을 연장하는 과정을 heap cell로 설명하라.

88. [구현] 작은 expression interpreter와 stack bytecode VM을 둘 다 만들라.

89. [비교] stack VM과 register VM의 bytecode 크기와 dispatch를 비교하라.

90. [구현] bytecode verifier로 jump target과 stack underflow를 검출하라.

91. [설명] static type, dynamic type, nominal, structural type의 차이를 예로 들라.

92. [설계] `Option<T>`나 nullable type에서 null error를 줄이는 API를 설계하라.

93. [설명] type erasure와 virtual dispatch, template monomorphization을 비교하라.

94. [구현] constant folding과 dead code after return 최적화를 추가하라.

95. [설명] SSA의 phi node가 control-flow merge에서 필요한 이유를 예로 들라.

96. [구현] basic block과 CFG를 만들고 unreachable block을 제거하라.

97. [실험] interpreter, bytecode VM, native compiled version의 성능을 비교하라.

98. [설명] undefined behavior가 optimizer에 주는 가정을 작은 C++ 예로 설명하라.

99. [비교] C++ RAII, Rust ownership, tracing GC의 자원 수명 모델을 비교하라.

100. [설명] Python object/reference model이 C++ value semantics와 다른 점을 쓰라.

101. [설계] C ABI를 가진 plugin interface와 version negotiation을 설계하라.

102. [fuzz] lexer/parser fuzz target을 만들고 최소 crash input을 보존하라.

103. [논문] LLVM 논문에서 IR와 compiler infrastructure의 핵심 설계를 정리하라.

104. [종합] Mori에 closure를 추가하면서 parser, resolver, bytecode, VM, GC가 어떻게 변하는지 문서화하라.



# 제5부 — 알고리즘과 데이터 구조


105. [증명] loop invariant로 insertion sort의 정확성을 설명하라.

106. [계산] 여러 함수의 Big-O, Big-Theta를 구하고 상수와 입력 범위를 함께 논하라.

107. [반례] 평균 O(1) hash lookup이 항상 빠르다는 주장에 반례를 들라.

108. [구현] dynamic array를 만들고 amortized push 비용을 실험하라.

109. [구현] open addressing hash table과 tombstone을 구현하라.

110. [실험] load factor에 따른 probe 길이 분포를 측정하라.

111. [구현] binary heap과 priority queue를 구현하라.

112. [설명] BST가 linked list로 퇴화하는 입력과 balanced tree 필요성을 설명하라.

113. [구현] union-find with path compression/rank를 만들고 naive와 비교하라.

114. [구현] stable merge sort와 unstable quicksort 결과를 record key로 비교하라.

115. [설명] quicksort pivot 전략과 worst case를 쓰라.

116. [구현] binary search에서 half-open interval 불변식을 사용하라.

117. [반례] overflow가 있는 `mid=(lo+hi)/2`의 문제를 설명하라.

118. [구현] BFS, DFS를 만들고 동일 그래프에서 방문 순서를 비교하라.

119. [구현] Dijkstra와 A*를 grid에 적용하고 heuristic 영향과 탐색 node 수를 측정하라.

120. [증명] A* heuristic admissibility가 최적성에 필요한 이유를 스케치하라.

121. [구현] topological sort와 cycle 진단을 만들라.

122. [구현] strongly connected components를 적용해 module cycle을 찾으라.

123. [설명] Bloom filter의 false positive와 false negative 성질을 설명하라.

124. [실험] Bloom filter bit 수/hash 수에 따른 false positive를 측정하라.

125. [구현] reservoir sampling으로 크기를 모르는 stream에서 k개를 뽑으라.

126. [설명] randomized algorithm의 기대 시간과 확정 시간 보장을 구분하라.

127. [실험] external merge sort를 memory limit 아래에서 구현하라.

128. [비교] pointer tree와 sorted vector의 lookup/update/cache 성능을 측정하라.

129. [설계] game entity lookup 요구에 맞춰 vector, hash, sparse set을 비교하라.

130. [종합] 알고리즘 하나를 느린 reference, 최적화 버전, property test, benchmark까지 완성하라.



# 제6부 — 네트워크, 데이터베이스, 분산


131. [설명] TCP가 message가 아니라 byte stream이라는 사실을 partial read 예로 보이라.

132. [구현] 4-byte length prefix framing encoder/decoder를 만들라.

133. [fuzz] 최대 길이와 partial frame을 처리하는 protocol parser를 fuzz하라.

134. [설명] UDP에서 위치 snapshot과 구매 요청의 reliability 정책이 달라야 하는 이유를 쓰라.

135. [설계] timeout, exponential backoff, jitter, retry budget을 가진 client를 설계하라.

136. [반례] timeout 후 재시도가 결제 중복을 만드는 trace를 작성하라.

137. [구현] idempotency key 저장과 결과 replay를 구현하라.

138. [설명] end-to-end argument를 file checksum 예로 설명하라.

139. [설계] versioned binary protocol의 unknown field/enum 정책을 정하라.

140. [SQL] player/inventory schema에 key와 constraint를 정의하라.

141. [분석] 한 query에 index 세 개 후보를 만들고 execution plan을 비교하라.

142. [설명] clustered/nonclustered 또는 primary/secondary index의 write 비용을 비교하라.

143. [trace] dirty read, non-repeatable read, phantom, write skew를 각각 재현하라.

144. [설계] 계좌 이체 불변식을 transaction과 constraint로 보호하라.

145. [설명] WAL에서 log와 data page flush 순서가 중요한 이유를 쓰라.

146. [구현] append-only KV store와 crash recovery를 만들라.

147. [실험] 마지막 record의 모든 byte 위치를 truncate하고 recovery를 검증하라.

148. [설명] Lamport clock의 `a→b이면 L(a)<L(b)`와 역이 성립하지 않음을 보이라.

149. [구현] vector clock으로 concurrent event를 구분하라.

150. [설명] linearizability와 serializability가 다른 대상의 성질인 이유를 쓰라.

151. [설계] eventual consistency에서 inventory count merge가 위험한 이유와 대안을 쓰라.

152. [설명] CAP를 ‘세 개 중 두 개’라는 문구보다 partition 상황의 선택으로 설명하라.

153. [구현] deterministic Raft election/log simulator를 만들라.

154. [검증] 두 committed value가 같은 log index에 존재하지 않는 invariant를 검사하라.

155. [실험] bounded queue와 load shedding이 overload latency에 미치는 영향을 측정하라.

156. [종합] 네트워크 지연·중복·crash 속에서도 안전한 아이템 구매 protocol을 설계하라.



# 제7부 — 아키텍처와 게임 구조


157. [분석] 한 파일 게임에서 숨겨진 변경 결정을 다섯 개 찾아 모듈 후보로 분류하라.

158. [리팩터링] 내부 `vector`를 노출하는 API를 능력 기반 API로 바꾸라.

159. [설계] ownership, error, unit, thread safety를 포함한 texture creation API를 작성하라.

160. [분석] 이름·자료구조·시간·수명·배포·실패 결합을 실제 프로젝트에서 찾아라.

161. [설계] 도메인 규칙이 DB 구현에 의존하지 않도록 dependency 방향을 바꾸라.

162. [반례] 인터페이스를 추가했지만 결합이 줄지 않는 예를 작성하라.

163. [설계] source, binary, behavior, data compatibility 표를 API 두 버전에 적용하라.

164. [구현] Idle/Run/Attack/Dodge/Stun/Dead 상태 머신을 구현하라.

165. [검증] Dead terminal, Dodge invulnerability, Stun priority를 test하라.

166. [리팩터링] 거대 Player class를 Health/Combat/Interaction component로 분리하라.

167. [구현] 값 타입 Command를 기록·재생하라.

168. [설계] direct call과 event queue를 선택하는 기준을 사례 세 개로 설명하라.

169. [디버깅] event bus에서 순서와 stale reference 문제를 재현하라.

170. [구현] generation handle pool을 만들고 slot reuse test를 작성하라.

171. [실험] object pool이 실제로 allocation 시간을 줄이는 조건을 측정하라.

172. [구현] fixed timestep과 interpolation loop를 작성하라.

173. [검증] 같은 seed/input log가 같은 state hash를 만드는지 확인하라.

174. [설계] system update dependency DAG를 만들고 cycle을 진단하라.

175. [비교] object actor, sparse-set ECS, archetype ECS의 workload를 설계해 비교하라.

176. [실험] AoS/SoA, hot/cold split의 entity update 성능을 측정하라.

177. [구현] immutable RenderSnapshot을 추출하라.

178. [구현] dependency와 help-waiting을 가진 작은 job system을 만들라.

179. [분석] job granularity를 바꾸며 overhead와 load balance를 측정하라.

180. [설계] source asset부터 cooked artifact까지 content hash pipeline을 설계하라.

181. [문서] 아키텍처 결정 하나를 ADR로 작성하고 대안과 수치를 포함하라.

182. [종합] 같은 기능을 단순 객체 구조와 data-oriented 구조로 구현해 변경성과 성능을 함께 비교하라.



# 제8부 — 품질, 디버깅, 성능


183. [테스트] 한 함수에 example, boundary, property test를 모두 작성하라.

184. [property] sort, serializer, handle pool의 불변식을 각각 정의하라.

185. [metamorphic] 정답 oracle 없는 그래픽/물리 기능의 변환 관계를 세 개 만들라.

186. [differential] 최적화 알고리즘을 느린 reference와 비교하라.

187. [fuzz] parser target에 ASan/UBSan을 결합하고 corpus를 관리하라.

188. [동시성] scheduler seed를 기록하는 race test harness를 설계하라.

189. [보고] 재현율·환경·최초 정상 commit이 포함된 bug report를 작성하라.

190. [축소] 큰 실패 scene을 delta debugging으로 최소화하라.

191. [도구] Git bisect를 자동 test와 함께 실행하라.

192. [디버깅] use-after-free의 allocation/free/use stack을 diagram으로 그리라.

193. [로그] 문자열 로그를 구조화 event와 correlation ID로 바꾸라.

194. [관찰] metric, log, trace가 각각 잡는 문제를 사례로 구분하라.

195. [GPU] frame capture에서 draw 하나의 pipeline/resource/shader를 추적하라.

196. [목표] 평균이 아닌 p50/p95/p99와 budget을 포함한 성능 요구를 작성하라.

197. [benchmark] compiler elimination과 warmup을 피하는 microbenchmark를 설계하라.

198. [계산] Amdahl 법칙으로 최적화 후보 세 개의 최대 효과를 구하라.

199. [분석] Roofline 관점에서 kernel의 arithmetic intensity를 추정하라.

200. [profiling] allocation flame graph를 얻고 상위 원인 하나를 수정하라.

201. [실험] false sharing 전후를 alignment/sharding으로 비교하라.

202. [GPU] 해상도, draw 수, shader 복잡도를 각각 바꿔 병목을 구분하라.

203. [보고] 최적화 전후 정확성·성능·trade-off 보고서를 작성하라.

204. [빌드] clean machine/container에서 one-command build를 만들라.

205. [재현성] 같은 source로 artifact hash가 달라지는 원인을 찾아 제거하라.

206. [CI] compiler matrix, sanitizer, test, package pipeline을 작성하라.

207. [review] 수명·동시성·오류·관찰 가능성 중심으로 실제 PR을 리뷰하라.

208. [논문] 한 논문의 핵심 실험을 축소 재현하고 원 결과와 차이를 분석하라.



# 제9부 — 보안과 신뢰성


209. [위협] 로그인·구매 시스템의 asset, actor, trust boundary를 작성하라.

210. [STRIDE] data flow diagram의 각 경계에 최소 한 위협을 찾으라.

211. [권한] 최소 권한을 위반하는 개발 도구를 찾아 권한을 줄이라.

212. [설계] fail-safe default와 explicit allow policy를 API에 적용하라.

213. [검증] 인증된 principal과 client-provided user ID를 혼동하는 결함을 재현하라.

214. [secret] source/log/build artifact에서 secret이 새는 경로를 조사하라.

215. [crypto] encryption, integrity, authentication, replay protection의 차이를 설명하라.

216. [parser] length overflow, nesting, decompression ratio 제한을 구현하라.

217. [path] traversal과 symlink race를 고려한 sandbox file API를 설계하라.

218. [injection] SQL/command/template injection을 구조화 API로 제거하라.

219. [게임] client가 damage를 결정하는 구조의 치트 trace와 server 검증을 설계하라.

220. [메모리] integer overflow 후 undersized allocation 결함을 test하라.

221. [도구] ASan, UBSan, TSan이 각각 잡는 오류와 못 잡는 오류를 표로 정리하라.

222. [격리] 비신뢰 asset importer를 제한된 process로 분리하라.

223. [공급망] dependency 하나의 maintainer, release, transitive dependency, script를 검토하라.

224. [SBOM] build artifact의 component/version/source를 기록하라.

225. [서명] update manifest와 payload의 signing/rotation/rollback 절차를 설계하라.

226. [plugin] data/script/native mod의 권한을 비교하고 capability API를 정하라.

227. [실패] crash-stop, crash-recovery, corruption, Byzantine 모델을 사례로 구분하라.

228. [deadline] 상위 deadline을 하위 호출에 전파하고 cancellation side effect를 처리하라.

229. [overload] unbounded queue로 retry storm을 재현하고 bounded admission으로 완화하라.

230. [backup] RPO/RTO를 정하고 자동 restore test를 작성하라.

231. [chaos] 작은 blast radius와 abort 조건이 있는 장애 실험 계획을 작성하라.

232. [incident] 실제 또는 가상 장애의 timeline과 기여 요인을 postmortem으로 쓰라.

233. [윤리] 수집 중인 telemetry 항목의 필요성·동의·보존·삭제를 검토하라.

234. [종합] signed build부터 배포, 관찰, rollback까지 공급망과 운영 threat model을 만들라.



# 제10부 — 게임, 그래픽스, 네트워크 게임, AI


235. [추적] input event가 display pixel에 반영될 때까지 CPU/GPU frame 경로를 그리라.

236. [실험] frames-in-flight 수와 input latency/throughput을 비교하라.

237. [설계] subsystem 초기화·종료 순서를 resource lifetime으로 설명하라.

238. [budget] CPU, GPU, memory, I/O budget을 target hardware에 작성하라.

239. [asset] async load callback에서 삭제된 entity를 참조하는 버그를 handle로 해결하라.

240. [설계] animation notify와 gameplay hit timing의 authoritative source를 정하라.

241. [수학] model/view/projection으로 점 하나를 screen까지 계산하라.

242. [설명] homogeneous divide와 perspective-correct interpolation을 설명하라.

243. [구현] CPU triangle rasterizer와 depth buffer를 만들라.

244. [구현] normal transform과 tangent-space normal mapping을 구현하라.

245. [셰이더] Lambert, Blinn-Phong, GGX subset을 구현하고 비교하라.

246. [색] sRGB texture를 linear로 처리하지 않았을 때 결과를 캡처하라.

247. [그림자] shadow bias를 바꾸며 acne와 peter-panning trade-off를 기록하라.

248. [비교] forward/deferred/clustered를 scene 조건별로 평가하라.

249. [HDR] exposure와 tone mapping curve를 구현하고 histogram을 분석하라.

250. [TAA] motion vector와 history rejection 없는 TAA의 ghosting을 재현하라.

251. [수명] GPU fence 전에 resource를 파괴하는 오류를 재현하고 deferred deletion을 구현하라.

252. [render graph] pass read/write 선언으로 dependency와 transient lifetime을 계산하라.

253. [GPU-driven] frustum culling과 indirect argument 생성의 CPU/GPU 비용을 비교하라.

254. [네트워크] client prediction/reconciliation simulator를 만들라.

255. [보간] jitter/loss 변화에 따른 interpolation delay와 error를 측정하라.

256. [replication] position/rotation quantization의 bandwidth와 오차를 비교하라.

257. [AI] behavior tree action cancellation과 trace를 구현하라.

258. [AI] utility score에 hysteresis가 없을 때 oscillation을 재현하라.

259. [ML] inference latency, model size, fallback을 포함한 실시간 ML feature를 설계하라.

260. [종합] AI가 생성한 shader/C++ 코드를 compile, fuzz, profile, visual regression으로 검증하라.



# 통합 문제


261. [종합 1] Tiny-8에 memory-mapped display를 추가하고 작은 sprite 명령을 실행하라.

262. [종합 2] Mori compiler가 Tiny-8 assembly를 출력하도록 최소 backend를 설계하라.

263. [종합 3] Mori script를 Apex gameplay에 sandbox로 넣고 instruction budget을 적용하라.

264. [종합 4] StoneKV에 Apex replay와 save data를 저장하고 schema migration을 구현하라.

265. [종합 5] Apex asset importer를 별도 process로 격리하고 content-addressed cache를 붙이라.

266. [종합 6] 동일한 simulation을 single-thread와 job system에서 실행해 state hash를 비교하라.

267. [종합 7] renderer를 CPU reference와 D3D12 두 backend로 구현해 image diff를 만들라.

268. [종합 8] 10만 entity benchmark에서 자료구조, cache, job granularity를 함께 분석하라.

269. [종합 9] 네트워크 prediction 중 rollback된 gameplay event가 audio를 중복 재생하는 문제를 해결하라.

270. [종합 10] 게임 구매 service의 transaction, idempotency, audit, threat model을 통합 설계하라.

271. [종합 11] GPU crash와 asset corruption이 동시에 발생한 incident를 진단하는 observability 설계를 하라.

272. [종합 12] compiler-generated bytecode를 비신뢰 입력으로 보고 verifier와 fuzzing을 설계하라.

273. [종합 13] 한 최적화가 보안을 약화시키는 사례를 찾고 대안을 평가하라.

274. [종합 14] 기능 하나를 monolith와 service 두 구조로 설계하고 실패 결합을 비교하라.

275. [종합 15] 현재 프로젝트의 dependency graph, runtime graph, data flow graph를 각각 작성하라.

276. [종합 16] 논문 하나의 알고리즘을 구현하되 원 가정과 자신의 환경 차이를 명시하라.

277. [종합 17] 24시간 soak test와 fault injection에서 수집할 SLI를 설계하라.

278. [종합 18] code review에서 발견한 결함을 compiler rule, test, API redesign 중 가장 싼 방식으로 예방하라.

279. [종합 19] 30분 기술 발표로 ‘bit에서 pixel까지’를 자신의 프로젝트 trace로 설명하라.

280. [종합 20] 네 프로젝트 중 하나를 빈 저장소에서 8시간 동안 핵심만 재구현하고 차이를 회고하라.


# 제출 양식


```text
문제 번호:
가설/설계:
구현 또는 증명:
실패한 첫 시도:
검증 도구:
측정 환경:
결과:
반례/한계:
다시 한다면:
```


총 문제 수: **280개**
