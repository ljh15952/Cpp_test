# 부록 C — 주석 달린 참고문헌과 논문 읽기 지도

이 목록은 본문의 주장을 뒷받침하고 더 깊은 학습 경로를 제공한다. 논문을 인용했다는 사실이 곧 주장이 옳다는 뜻은 아니다. 원문의 가정, workload, 시대의 hardware, 후속 반례를 함께 확인한다.

표시:

- **[기초]** 핵심 개념의 원류
- **[구현]** 실제 시스템을 만들 때 직접 도움
- **[연구]** 심화·전문 분야
- **[사양]** 현재 동작을 정의하는 규범 문서

# C.1 계산, 정보, 컴퓨터 역사

1. **[기초] Alan M. Turing, “On Computable Numbers, with an Application to the Entscheidungsproblem,” 1936.** 계산 가능성을 machine model로 형식화한다. [PDF](https://www.cs.virginia.edu/~robins/Turing_Paper_1936.pdf)
2. **[기초] Alonzo Church, “An Unsolvable Problem of Elementary Number Theory,” 1936.** 계산 가능성의 독립적 형식화와 결정 불가능성. [JSTOR/DOI](https://doi.org/10.2307/2371045)
3. **[기초] Claude E. Shannon, “A Symbolic Analysis of Relay and Switching Circuits,” 1937.** Boolean algebra와 switching circuit의 연결. [MIT DSpace](https://dspace.mit.edu/handle/1721.1/11173)
4. **[기초] John von Neumann, “First Draft of a Report on the EDVAC,” 1945.** 저장 프로그램식 전자 계산기의 조직. [PDF](https://web.mit.edu/STS.035/www/PDFs/edvac.pdf)
5. **[기초] Claude E. Shannon, “A Mathematical Theory of Communication,” 1948.** entropy, channel, coding의 기초. [PDF](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf)
6. **[역사] Vannevar Bush, “As We May Think,” 1945.** 정보 접근과 연상 구조에 대한 역사적 비전. [The Atlantic](https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/)
7. **[역사] Gordon E. Moore, “Cramming More Components onto Integrated Circuits,” 1965.** 집적도 추세의 원문. [PDF](https://www.cs.utexas.edu/~fussell/courses/cs352h/papers/moore.pdf)
8. **[역사] Computer History Museum, “Timeline of Computer History.”** 기계·제품·인물의 검증 가능한 연표 자료. [Timeline](https://www.computerhistory.org/timeline/)
9. **[기초] John Backus, “Can Programming Be Liberated from the von Neumann Style?” 1978.** 명령형 병목과 함수형 대안에 대한 Turing Award 강연. [DOI](https://doi.org/10.1145/359576.359579)
10. **[기초] Edsger W. Dijkstra, “The Humble Programmer,” 1972.** 프로그램 복잡성과 인간의 한계를 다루는 Turing Award 강연. [EWD340](https://www.cs.utexas.edu/users/EWD/transcriptions/EWD03xx/EWD340.html)
11. **[역사] Dennis M. Ritchie, “The Development of the C Language,” 1993.** C와 Unix의 상호 발전. [Bell Labs PDF](https://www.bell-labs.com/usr/dmr/www/chist.html)
12. **[역사] Richard M. Stallman, “The GNU Manifesto,” 1985.** 자유 소프트웨어 운동의 역사적 문서. [GNU](https://www.gnu.org/gnu/manifesto.html)

# C.2 컴퓨터 구조, 메모리, 성능

13. **[기초] Gene M. Amdahl, “Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities,” 1967.** 부분 최적화의 전체 한계. [DOI](https://doi.org/10.1145/1465482.1465560)
14. **[기초] John L. Hennessy & David A. Patterson, *Computer Architecture: A Quantitative Approach*.** 측정과 trade-off 중심의 구조 교과서.
15. **[기초] David A. Patterson & John L. Hennessy, *Computer Organization and Design*.** ISA, datapath, memory hierarchy 입문.
16. **[연구] Tomasulo, “An Efficient Algorithm for Exploiting Multiple Arithmetic Units,” 1967.** 동적 scheduling과 register renaming의 고전. [IBM Research](https://research.ibm.com/publications/an-efficient-algorithm-for-exploiting-multiple-arithmetic-units)
17. **[기초] Peter J. Denning, “The Working Set Model for Program Behavior,” 1968.** locality와 virtual memory working set. [DOI](https://doi.org/10.1145/363095.363141)
18. **[구현] Ulrich Drepper, “What Every Programmer Should Know About Memory,” 2007.** cache, NUMA, memory 성능의 상세 해설. [PDF](https://people.freebsd.org/~lstewart/articles/cpumemory.pdf)
19. **[연구] Samuel Williams, Andrew Waterman, David Patterson, “Roofline,” 2009.** 연산량과 memory bandwidth의 상한 모델. [PDF](https://crd.lbl.gov/assets/pubs_presos/roofline-hpca09.pdf)
20. **[연구] Mark D. Hill & Michael R. Marty, “Amdahl’s Law in the Multicore Era,” 2008.** multicore 자원 배분과 Amdahl 확장. [DOI](https://doi.org/10.1109/MC.2008.209)
21. **[연구] Norman P. Jouppi, “Improving Direct-Mapped Cache Performance by the Addition of a Small Fully-Associative Cache and Prefetch Buffers,” 1990.** victim cache와 prefetch. [DOI](https://doi.org/10.1145/325164.325162)
22. **[사양] RISC-V International, “The RISC-V Instruction Set Manual.”** 공개 ISA의 현재 규범 사양. [Specifications](https://riscv.org/technical/specifications/)
23. **[구현] Agner Fog, “Optimizing Software in C++” 및 instruction tables.** microarchitecture 실험과 최적화 참고. [자료](https://www.agner.org/optimize/)
24. **[연구] Kim et al., “Flipping Bits in Memory Without Accessing Them: An Experimental Study of DRAM Disturbance Errors,” 2014.** Rowhammer와 hardware reliability. [PDF](https://users.ece.cmu.edu/~yoonguk/papers/kim-isca14.pdf)

# C.3 운영체제, 동시성, 검증

25. **[기초] Edsger W. Dijkstra, “The Structure of the ‘THE’ Multiprogramming System,” 1968.** 계층화된 OS 설계. [EWD196](https://www.cs.utexas.edu/users/EWD/ewd01xx/EWD196.PDF)
26. **[기초] Butler Lampson, “Hints for Computer System Design,” 1983.** 시스템 설계의 압축된 경험. [PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/acrobat-17.pdf)
27. **[기초] Saltzer & Schroeder, “The Protection of Information in Computer Systems,” 1975.** 최소 권한 등 보호 원칙. [원문](https://web.mit.edu/Saltzer/www/publications/protection/)
28. **[기초] Saltzer, Reed, Clark, “End-to-End Arguments in System Design,” 1984.** 기능 배치와 endpoint 검증. [PDF](https://web.mit.edu/Saltzer/www/publications/endtoend/endtoend.pdf)
29. **[기초] C. A. R. Hoare, “Monitors: An Operating System Structuring Concept,” 1974.** monitor와 condition synchronization. [DOI](https://doi.org/10.1145/355620.361161)
30. **[기초] Leslie Lamport, “Time, Clocks, and the Ordering of Events in a Distributed System,” 1978.** happens-before와 logical clock. [PDF](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)
31. **[기초] Herlihy & Wing, “Linearizability: A Correctness Condition for Concurrent Objects,” 1990.** concurrent object의 관찰 가능한 원자성. [PDF](https://cs.brown.edu/~mph/HerlihyW90/p463-herlihy.pdf)
32. **[연구] Boehm, “Threads Cannot Be Implemented as a Library,” 2005.** language memory model이 필요한 이유. [PDF](https://www.hboehm.info/misc_slides/pldi05_threads.pdf)
33. **[연구] Maged M. Michael, “Hazard Pointers,” 2004.** lock-free reclamation. [DOI](https://doi.org/10.1109/TPDS.2004.8)
34. **[연구] Fraser, “Practical Lock-Freedom,” 2004.** lock-free 자료구조와 memory reclamation. [PDF](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-579.pdf)
35. **[연구] Klein et al., “seL4: Formal Verification of an OS Kernel,” 2009.** 실제 kernel의 기계 검증. [PDF](https://sel4.systems/Research/pdfs/seL4-formal-verification.pdf)
36. **[구현] Remzi & Andrea Arpaci-Dusseau, *Operating Systems: Three Easy Pieces*.** 무료 운영체제 교과서와 실습. [OSTEP](https://pages.cs.wisc.edu/~remzi/OSTEP/)
37. **[연구] Liedtke, “On Micro-Kernel Construction,” 1995.** IPC 비용과 microkernel 설계. [PDF](https://os.itec.kit.edu/downloads/publ_1995_liedtke_ukernel-construction.pdf)
38. **[연구] Engler et al., “Exokernel,” 1995.** application-level resource management. [PDF](https://pdos.csail.mit.edu/6.828/2008/readings/engler95exokernel.pdf)

# C.4 프로그래밍 언어, 컴파일러, 메모리 관리

39. **[기초] C. A. R. Hoare, “An Axiomatic Basis for Computer Programming,” 1969.** pre/postcondition과 프로그램 논리. [PDF](https://www.cs.cmu.edu/~crary/819-f09/Hoare69.pdf)
40. **[기초] Dijkstra, “Guarded Commands, Nondeterminacy and Formal Derivation of Programs,” 1975.** 명세와 프로그램 도출. [EWD472](https://www.cs.utexas.edu/users/EWD/transcriptions/EWD04xx/EWD472.html)
41. **[기초] Peter J. Landin, “The Next 700 Programming Languages,” 1966.** 언어 구조를 작은 core로 보는 관점. [DOI](https://doi.org/10.1145/365230.365257)
42. **[기초] Steele & Sussman, “Lambda: The Ultimate Imperative,” 1976.** lexical scope와 continuation을 통한 언어 해석. [PDF](https://dspace.mit.edu/bitstream/handle/1721.1/5790/AIM-353.pdf)
43. **[기초] Guy L. Steele Jr., “Growing a Language,” 1998.** 언어와 추상화가 성장하는 방식. [영상/문서](https://www.cs.virginia.edu/~evans/cs655/readings/steele.pdf)
44. **[연구] Cytron et al., “Efficiently Computing Static Single Assignment Form and the Control Dependence Graph,” 1991.** SSA 구성의 고전. [PDF](https://www.cs.utexas.edu/~pingali/CS380C/2019/papers/ssa.pdf)
45. **[구현] Chris Lattner & Vikram Adve, “LLVM: A Compilation Framework for Lifelong Program Analysis & Transformation,” 2004.** 현대 compiler infrastructure. [PDF](https://llvm.org/pubs/2004-01-30-CGO-LLVM.pdf)
46. **[기초] Wilson, “Uniprocessor Garbage Collection Techniques,” 1992.** GC 기법 survey. [PDF](https://www.cs.utexas.edu/users/oops/papers/gcsurvey.pdf)
47. **[연구] Bacon, Cheng, Rajan, “A Real-Time Garbage Collector with Low Overhead and Consistent Utilization,” 2003.** 실시간 GC trade-off. [DOI](https://doi.org/10.1145/949305.949336)
48. **[연구] Jung et al., “RustBelt: Securing the Foundations of the Rust Programming Language,” 2018.** unsafe abstraction의 논리적 검증. [PDF](https://plv.mpi-sws.org/rustbelt/popl18/paper.pdf)
49. **[사양] ISO C++ Working Draft.** 현재 C++ 표준 초안. [eel.is mirror](https://eel.is/c++draft/)
50. **[사양] The Rust Reference.** Rust 언어의 규범적 설명. [Reference](https://doc.rust-lang.org/reference/)
51. **[사양] Python Language Reference.** execution model과 data model의 공식 문서. [Docs](https://docs.python.org/3/reference/)
52. **[구현] Bob Nystrom, *Crafting Interpreters*.** tree-walk interpreter와 bytecode VM의 공개 교재. [온라인](https://craftinginterpreters.com/)
53. **[구현] Appel, *Modern Compiler Implementation*.** compiler phase와 runtime의 구현 교재.
54. **[구현] Aho, Lam, Sethi, Ullman, *Compilers: Principles, Techniques, and Tools*.** parsing, optimization의 고전 교재.
55. **[연구] Leroy, “Formal Verification of a Realistic Compiler,” 2009.** CompCert와 semantic preservation. [PDF](https://xavierleroy.org/publi/compcert-CACM.pdf)
56. **[연구] Sewell et al., “x86-TSO,” 2010.** x86 multiprocessor memory model의 수학적·실험적 모델. [PDF](https://www.cl.cam.ac.uk/~pes20/weakmemory/cacm.pdf)

# C.5 알고리즘과 데이터 구조

57. **[기초] Dijkstra, “A Note on Two Problems in Connexion with Graphs,” 1959.** shortest path 알고리즘의 원문. [PDF](https://www.cs.utexas.edu/~EWD/ewd00xx/EWD6.PDF)
58. **[기초] Hart, Nilsson, Raphael, “A Formal Basis for the Heuristic Determination of Minimum Cost Paths,” 1968.** A*. [PDF](https://ai.stanford.edu/~nilsson/OnlinePubs-Nils/PublishedPapers/astar.pdf)
59. **[기초] Bayer & McCreight, “Organization and Maintenance of Large Ordered Indexes,” 1972.** B-tree. [DOI](https://doi.org/10.1007/BF00288683)
60. **[기초] Bloom, “Space/Time Trade-offs in Hash Coding with Allowable Errors,” 1970.** Bloom filter. [DOI](https://doi.org/10.1145/362686.362692)
61. **[기초] Tarjan, “Efficiency of a Good But Not Linear Set Union Algorithm,” 1975.** union-find 분석. [DOI](https://doi.org/10.1145/321879.321884)
62. **[기초] Pugh, “Skip Lists: A Probabilistic Alternative to Balanced Trees,” 1990.** skip list. [PDF](https://homepage.cs.uiowa.edu/~ghosh/skip.pdf)
63. **[연구] Pagh & Rodler, “Cuckoo Hashing,” 2001.** worst-case lookup과 relocation. [PDF](https://www.itu.dk/people/pagh/papers/cuckoo-jour.pdf)
64. **[연구] Cormode & Muthukrishnan, “An Improved Data Stream Summary: The Count-Min Sketch,” 2005.** streaming frequency approximation. [PDF](https://dimacs.rutgers.edu/~graham/pubs/papers/cm-full.pdf)
65. **[연구] Flajolet et al., “HyperLogLog,” 2007.** cardinality estimation. [PDF](https://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf)
66. **[기초] Vitter, “Random Sampling with a Reservoir,” 1985.** reservoir sampling. [PDF](https://www.cs.umd.edu/~samir/498/vitter.pdf)
67. **[연구] Frigo et al., “Cache-Oblivious Algorithms,” 1999.** cache parameter를 코드에 박지 않는 locality 설계. [PDF](https://supertech.csail.mit.edu/papers/Prokop99.pdf)
68. **[연구] Leis et al., “The Adaptive Radix Tree,” 2013.** modern CPU에서 index 구조. [PDF](https://db.in.tum.de/~leis/papers/ART.pdf)
69. **[구현] Cormen, Leiserson, Rivest, Stein, *Introduction to Algorithms*.** 증명과 표준 알고리즘.
70. **[구현] Sedgewick & Wayne, *Algorithms*.** 구현·실험 중심 참고서.

# C.6 데이터베이스, 네트워크, 분산 시스템

71. **[기초] E. F. Codd, “A Relational Model of Data for Large Shared Data Banks,” 1970.** 관계형 모델. [PDF](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf)
72. **[기초] Gray et al., “Granularity of Locks and Degrees of Consistency in a Shared Data Base,” 1976.** lock granularity와 isolation. [PDF](https://jimgray.azurewebsites.net/papers/Granularity%20of%20Locks%20and%20Degrees%20of%20Consistency%20RJ%201654.pdf)
73. **[기초] Mohan et al., “ARIES,” 1992.** WAL 기반 recovery의 고전. [PDF](https://www.cs.cornell.edu/courses/cs5414/2017fa/papers/aries.pdf)
74. **[기초] O’Neil et al., “The Log-Structured Merge-Tree,” 1996.** write-optimized storage. [PDF](https://www.cs.umb.edu/~poneil/lsmtree.pdf)
75. **[구현] SQLite, “Atomic Commit in SQLite.”** 실제 파일·journal commit protocol. [문서](https://www.sqlite.org/atomiccommit.html)
76. **[사양] Eddy, “Transmission Control Protocol,” RFC 9293, 2022.** 현재 TCP base specification. [RFC](https://www.rfc-editor.org/rfc/rfc9293)
77. **[사양] Fielding et al., “HTTP Semantics,” RFC 9110, 2022.** HTTP 의미. [RFC](https://www.rfc-editor.org/rfc/rfc9110)
78. **[사양] Iyengar & Thomson, “QUIC,” RFC 9000, 2021.** QUIC transport. [RFC](https://www.rfc-editor.org/rfc/rfc9000)
79. **[기초] Lamport, “The Part-Time Parliament,” 1998.** Paxos의 원 논문. [PDF](https://lamport.azurewebsites.net/pubs/lamport-paxos.pdf)
80. **[기초] Lamport, “Paxos Made Simple,” 2001.** 합의 알고리즘의 간결한 해설. [PDF](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf)
81. **[기초] Ongaro & Ousterhout, “In Search of an Understandable Consensus Algorithm (Raft),” 2014.** leader 기반 consensus. [PDF](https://raft.github.io/raft.pdf)
82. **[기초] Fischer, Lynch, Paterson, “Impossibility of Distributed Consensus with One Faulty Process,” 1985.** 비동기 consensus의 한계. [PDF](https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf)
83. **[기초] Chandy & Lamport, “Distributed Snapshots,” 1985.** 일관된 global snapshot. [PDF](https://lamport.azurewebsites.net/pubs/chandy.pdf)
84. **[기초] Fidge, “Timestamps in Message-Passing Systems That Preserve the Partial Ordering,” 1988.** vector clock 계열. [PDF](https://fileadmin.cs.lth.se/cs/Personal/Amr_Ergawy/dist-algos-papers/4.pdf)
85. **[기초] Gilbert & Lynch, “Brewer’s Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services,” 2002.** CAP의 형식화. [PDF](https://users.ece.cmu.edu/~adrian/731-sp04/readings/GL-cap.pdf)
86. **[연구] Shapiro et al., “Conflict-Free Replicated Data Types,” 2011.** CRDT. [PDF](https://inria.hal.science/inria-00609399/document)
87. **[구현] Dean & Ghemawat, “MapReduce,” 2004.** 대규모 batch processing. [PDF](https://static.googleusercontent.com/media/research.google.com/en//archive/mapreduce-osdi04.pdf)
88. **[구현] Ghemawat, Gobioff, Leung, “The Google File System,” 2003.** commodity failure 환경의 분산 파일 시스템. [PDF](https://static.googleusercontent.com/media/research.google.com/en//archive/gfs-sosp2003.pdf)
89. **[구현] Chang et al., “Bigtable,” 2006.** 분산 structured storage. [PDF](https://static.googleusercontent.com/media/research.google.com/en//archive/bigtable-osdi06.pdf)
90. **[구현] DeCandia et al., “Dynamo,” 2007.** availability 중심 key-value store. [PDF](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
91. **[구현] Corbett et al., “Spanner,” 2012.** global transactions와 TrueTime. [PDF](https://research.google/pubs/pub39966/)
92. **[구현] Dean & Barroso, “The Tail at Scale,” 2013.** tail latency와 redundancy. [PDF](https://research.google/pubs/pub40801/)
93. **[구현] Sigelman et al., “Dapper,” 2010.** 대규모 분산 tracing. [PDF](https://research.google/pubs/pub36356/)
94. **[연구] Bailis et al., “Highly Available Transactions: Virtues and Limitations,” 2014.** availability와 transaction semantics. [PDF](https://www.vldb.org/pvldb/vol7/p181-bailis.pdf)

# C.7 소프트웨어 설계, 테스트, 디버깅

95. **[기초] David L. Parnas, “On the Criteria To Be Used in Decomposing Systems into Modules,” 1972.** 정보 은닉에 따른 모듈화. [PDF](https://www.cs.umd.edu/class/spring2003/cmsc838p/Design/criteria.pdf)
96. **[기초] Dijkstra, “Go To Statement Considered Harmful,” 1968.** 제어 흐름과 추론 가능성. [PDF](https://www.cs.utexas.edu/users/EWD/ewd02xx/EWD215.PDF)
97. **[기초] Frederick P. Brooks Jr., “No Silver Bullet,” 1987.** software의 본질적·우발적 복잡성. [PDF](https://www.cs.unc.edu/techreports/86-020.pdf)
98. **[기초] Gamma, Helm, Johnson, Vlissides, *Design Patterns*, 1994.** 객체지향 설계 패턴의 공통 언어.
99. **[구현] Robert Nystrom, *Game Programming Patterns*.** 게임 loop·state·component·event의 공개 교재. [온라인](https://gameprogrammingpatterns.com/)
100. **[연구] Claessen & Hughes, “QuickCheck,” 2000.** property-based testing. [PDF](https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf)
101. **[연구] Miller et al., “An Empirical Study of the Reliability of UNIX Utilities,” 1990.** 초기 fuzz testing. [PDF](https://pages.cs.wisc.edu/~bart/fuzz/CS736-Projects-f1988.pdf)
102. **[구현] Serebryany et al., “AddressSanitizer,” 2012.** memory error detection. [PDF](https://www.usenix.org/system/files/conference/atc12/atc12-final39.pdf)
103. **[연구] Nethercote & Seward, “Valgrind,” 2007.** dynamic binary instrumentation. [PDF](https://valgrind.org/docs/valgrind2007.pdf)
104. **[연구] Zeller & Hildebrandt, “Simplifying and Isolating Failure-Inducing Input,” 2002.** delta debugging. [PDF](https://www.st.cs.uni-saarland.de/publications/files/zeller-tse-2002.pdf)
105. **[연구] Yang et al., “Finding and Understanding Bugs in C Compilers,” 2011.** Csmith와 differential testing. [PDF](https://www.cs.utah.edu/~regehr/papers/pldi11-preprint.pdf)
106. **[연구] Regehr et al., “Test-Case Reduction for C Compiler Bugs,” 2012.** C-Reduce. [PDF](https://www.cs.utah.edu/~regehr/papers/pldi12-preprint.pdf)
107. **[구현] Google, *Site Reliability Engineering*.** SLO, incident, 운영 자동화의 공개 교재. [온라인](https://sre.google/sre-book/table-of-contents/)
108. **[구현] Beyer et al., *The Site Reliability Workbook*.** SRE 실전 운영. [온라인](https://sre.google/workbook/table-of-contents/)
109. **[연구] Leveson & Turner, “An Investigation of the Therac-25 Accidents,” 1993.** software와 system safety의 고전 사례. [PDF](https://sunnyday.mit.edu/papers/therac.pdf)

# C.8 보안과 공급망

110. **[기초] Anderson, “Why Cryptosystems Fail,” 1993.** primitive보다 운영·시스템 실패를 분석. [PDF](https://www.cl.cam.ac.uk/~rja14/Papers/wcf.pdf)
111. **[연구] Kocher et al., “Spectre Attacks,” 2019.** speculative execution side channel. [PDF](https://spectreattack.com/spectre.pdf)
112. **[연구] Lipp et al., “Meltdown,” 2018.** 권한 경계와 microarchitecture side channel. [PDF](https://meltdownattack.com/meltdown.pdf)
113. **[연구] Watson et al., “CHERI: A Hybrid Capability-System Architecture,” 2015.** hardware capability와 memory protection. [PDF](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-876.pdf)
114. **[사양] NIST, Secure Software Development Framework (SSDF), SP 800-218.** secure development practice. [문서](https://csrc.nist.gov/publications/detail/sp/800-218/final)
115. **[사양] OWASP Application Security Verification Standard.** application security 요구사항. [ASVS](https://owasp.org/www-project-application-security-verification-standard/)
116. **[사양] SLSA, Supply-chain Levels for Software Artifacts.** build provenance와 공급망 단계. [SLSA](https://slsa.dev/)
117. **[구현] Reproducible Builds Project.** 재현 가능한 binary를 위한 practice와 도구. [사이트](https://reproducible-builds.org/)
118. **[구현] The Update Framework (TUF) Specification.** software update의 key compromise·rollback 방어. [Specification](https://theupdateframework.github.io/specification/latest/)
119. **[연구] Wheeler, “Countering Trusting Trust through Diverse Double-Compiling,” 2005.** compiler 공급망 신뢰 검증. [PDF](https://dwheeler.com/trusting-trust/dissertation/wheeler-trusting-trust-ddc.pdf)
120. **[연구] Cowan et al., “StackGuard,” 1998.** stack smashing 방어의 초기 연구. [PDF](https://www.usenix.org/legacy/publications/library/proceedings/sec98/full_papers/cowan/cowan.pdf)

# C.9 실시간 그래픽스와 게임 엔진

121. **[기초] Phong, “Illumination for Computer Generated Pictures,” 1975.** 경험적 local illumination. [DOI](https://doi.org/10.1145/360825.360839)
122. **[기초] Cook & Torrance, “A Reflectance Model for Computer Graphics,” 1982.** microfacet reflectance의 고전. [DOI](https://doi.org/10.1145/357290.357293)
123. **[기초] Kajiya, “The Rendering Equation,” 1986.** light transport의 통합 방정식. [PDF](https://www.cs.northwestern.edu/~ago820/cs395/Papers/Kajiya_1986.pdf)
124. **[연구] Walter et al., “Microfacet Models for Refraction through Rough Surfaces,” 2007.** GGX 분포와 rough transmission. [PDF](https://www.cs.cornell.edu/~srm/publications/EGSR07-btdf.pdf)
125. **[구현] Brent Burley, “Physically-Based Shading at Disney,” 2012.** artist-friendly principled material. [PDF](https://disneyanimation.com/publications/physically-based-shading-at-disney/)
126. **[구현] Brian Karis, “Real Shading in Unreal Engine 4,” 2013.** game PBR와 IBL 근사. [PDF](https://cdn2.unrealengine.com/Resources/files/2013SiggraphPresentationsNotes-26915738.pdf)
127. **[연구] Olsson, Billeter, Assarsson, “Clustered Deferred and Forward Shading,” 2012.** 3D light clustering. [PDF](https://www.cse.chalmers.se/~uffe/clustered_shading_preprint.pdf)
128. **[구현] Karis, “High Quality Temporal Supersampling,” 2014.** UE4 temporal anti-aliasing. [PDF](https://de45xmedrsdbp.cloudfront.net/Resources/files/TemporalAA_small-59732822.pdf)
129. **[연구] Schied et al., “Spatiotemporal Variance-Guided Filtering,” 2017.** 실시간 path-traced denoising. [NVIDIA Research](https://research.nvidia.com/publication/2017-07_spatiotemporal-variance-guided-filtering-real-time-reconstruction-path-traced)
130. **[연구] Bitterli et al., “Spatiotemporal Reservoir Resampling for Real-Time Ray Tracing with Dynamic Direct Lighting,” 2020.** ReSTIR. [PDF](https://research.nvidia.com/publication/2020-07_spatiotemporal-reservoir-resampling-real-time-ray-tracing-dynamic-direct)
131. **[연구] Heitz et al., “Real-Time Polygonal-Light Shading with Linearly Transformed Cosines,” 2016.** LTC area lights. [Project](https://eheitzresearch.wordpress.com/415-2/)
132. **[연구] McGuire et al., “A Scalable and Production Ready Sky and Atmosphere Rendering Technique,” 2020.** atmosphere rendering. [PDF](https://sebh.github.io/publications/egsr2020.pdf)
133. **[구현] Yuriy O’Donnell, “FrameGraph: Extensible Rendering Architecture in Frostbite,” GDC 2017.** pass/resource graph. [PDF](https://www.gdcvault.com/play/1024612/FrameGraph-Extensible-Rendering-Architecture-in)
134. **[구현] McGuire & Bavoil, “Weighted Blended Order-Independent Transparency,” 2013.** 실용 OIT 근사. [PDF](https://jcgt.org/published/0002/02/09/paper.pdf)
135. **[연구] Jimenez et al., “Practical Real-Time Strategies for Accurate Indirect Occlusion,” 2016.** GTAO. [PDF](https://iryjo.github.io/publications/2016_gtao.pdf)
136. **[사양] Microsoft, Direct3D 12 Programming Guide.** explicit graphics API의 현재 공식 문서. [문서](https://learn.microsoft.com/windows/win32/direct3d12/directx-12-programming-guide)
137. **[사양] Microsoft DirectX Specifications: Mesh Shader, Work Graphs 등.** 기능별 규범 사양. [사양 저장소](https://microsoft.github.io/DirectX-Specs/)
138. **[구현] Microsoft, DirectX Graphics Samples.** D3D12 공식 sample code. [GitHub](https://github.com/microsoft/DirectX-Graphics-Samples)
139. **[구현] Tomas Akenine-Möller, Eric Haines, Naty Hoffman, *Real-Time Rendering*.** 실시간 그래픽스 종합 교과서.
140. **[구현] Matt Pharr, Wenzel Jakob, Greg Humphreys, *Physically Based Rendering*.** reference renderer와 수학. [온라인](https://pbr-book.org/)
141. **[구현] Christer Ericson, *Real-Time Collision Detection*.** geometry query와 robust collision.
142. **[구현] Jason Gregory, *Game Engine Architecture*.** 게임 엔진 subsystem 개관.
143. **[구현] Glenn Fiedler, “Fix Your Timestep!”** 고정 시간 simulation과 accumulator. [글](https://gafferongames.com/post/fix_your_timestep/)
144. **[구현] Glenn Fiedler, “Networked Physics.”** prediction, state synchronization의 실무 글. [모음](https://gafferongames.com/categories/networked-physics/)
145. **[구현] Epic Games, Unreal Engine Gameplay Framework Documentation.** engine의 현재 객체 역할. [문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-framework-in-unreal-engine)
146. **[구현] Epic Games, Unreal Insights Documentation.** task/frame trace와 성능 분석. [문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine)

# C.10 AI, 머신러닝 시스템, 인간과 도구

147. **[기초] Rumelhart, Hinton, Williams, “Learning Representations by Back-Propagating Errors,” 1986.** backpropagation의 고전. [PDF](https://www.cs.toronto.edu/~hinton/absps/naturebp.pdf)
148. **[연구] Krizhevsky, Sutskever, Hinton, “ImageNet Classification with Deep Convolutional Neural Networks,” 2012.** AlexNet. [PDF](https://proceedings.neurips.cc/paper_files/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf)
149. **[연구] He et al., “Deep Residual Learning for Image Recognition,” 2016.** ResNet. [PDF](https://arxiv.org/pdf/1512.03385)
150. **[연구] Vaswani et al., “Attention Is All You Need,” 2017.** Transformer. [PDF](https://arxiv.org/pdf/1706.03762)
151. **[연구] Mnih et al., “Human-level Control through Deep Reinforcement Learning,” 2015.** DQN. [Nature](https://doi.org/10.1038/nature14236)
152. **[연구] Silver et al., “Mastering the Game of Go with Deep Neural Networks and Tree Search,” 2016.** AlphaGo. [Nature](https://doi.org/10.1038/nature16961)
153. **[구현] Sculley et al., “Hidden Technical Debt in Machine Learning Systems,” 2015.** ML production의 시스템 부채. [PDF](https://papers.nips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf)
154. **[구현] Breck et al., “The ML Test Score,” 2017.** production ML readiness checklist. [PDF](https://research.google/pubs/pub46555/)
155. **[윤리] Gebru et al., “Datasheets for Datasets,” 2021.** dataset 문서화. [PDF](https://arxiv.org/pdf/1803.09010)
156. **[윤리] Mitchell et al., “Model Cards for Model Reporting,” 2019.** model의 용도·한계 보고. [PDF](https://arxiv.org/pdf/1810.03993)
157. **[연구] Ouyang et al., “Training Language Models to Follow Instructions with Human Feedback,” 2022.** instruction tuning과 RLHF. [PDF](https://arxiv.org/pdf/2203.02155)
158. **[연구] Chen et al., “Evaluating Large Language Models Trained on Code,” 2021.** code generation 평가와 한계. [PDF](https://arxiv.org/pdf/2107.03374)
159. **[연구] Pearce et al., “Asleep at the Keyboard? Assessing the Security of GitHub Copilot’s Code Contributions,” 2022.** 생성 코드 보안 평가. [PDF](https://arxiv.org/pdf/2108.09293)
160. **[구현] Google, “Rules of Machine Learning.”** ML system 구축의 실용 원칙. [문서](https://developers.google.com/machine-learning/guides/rules-of-ml)

# C.11 읽기 순서

## 1단계: 기반 12편

Turing, Shannon switching, EDVAC, Dijkstra THE, Parnas, Hoare, Codd, Lamport clocks, end-to-end, QuickCheck, Kajiya, Hidden Technical Debt를 먼저 읽는다. 모든 수식을 이해하려 하지 말고 문제·가정·핵심 아이디어·한계를 카드로 만든다.

## 2단계: 프로젝트에 따라 선택

- Tiny-8: 13–24
- Mori: 39–56
- StoneKV: 71–94
- Apex/게임: 121–146
- 보안: 110–120
- AI 기능: 147–160

## 3단계: 재현

읽은 자료 하나마다 다음 중 하나를 만든다.

- 100줄 이하 최소 구현
- 원 그림/표 하나의 축소 재현
- 반례
- 자신의 workload에서 benchmark
- 후속 논문과의 차이표

## 출처를 인용하는 방식

```text
주장: 무엇을 말하는가
출처: 원 논문/사양의 section
적용 조건: 어떤 hardware/workload/실패 모델인가
내 결과: 같은가, 다른가
한계: 무엇을 측정하지 못했는가
```

긴 문장을 그대로 옮기지 말고, 자신의 말로 정확히 요약하며 페이지·section·URL을 남긴다.
