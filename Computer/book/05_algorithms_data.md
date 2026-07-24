# 제5부 — 알고리즘과 데이터 구조

# 25장. 복잡도, 불변식, 증명

## 25.1 알고리즘을 평가하는 세 축

1. **정확성**: 모든 허용 입력에서 요구 결과를 내는가?
2. **복잡도**: 입력 크기에 따라 시간과 공간이 어떻게 증가하는가?
3. **현실 비용**: 캐시, 할당, 병렬성, I/O, 상수 계수는 어떠한가?

Big-O 하나로 모든 성능을 설명할 수 없다. 하지만 성장률을 무시하면 작은 테스트에서만 빠른 알고리즘을 선택할 수 있다.

## 25.2 점근 표기

- `O(g(n))`: 충분히 큰 n에서 상한
- `Ω(g(n))`: 하한
- `Θ(g(n))`: 같은 차수의 상·하한

선형 탐색은 최악 `Θ(n)`, 평균은 분포 가정에 따라 달라진다. 해시 테이블 조회를 무조건 O(1)이라고 말하기보다 평균·최악 조건과 해시 품질을 함께 말한다.

## 25.3 루프 불변식

삽입 정렬:

```cpp
void insertion_sort(std::span<int> values) {
    for (std::size_t i = 1; i < values.size(); ++i) {
        const int key = values[i];
        std::size_t j = i;
        while (j > 0 && values[j - 1] > key) {
            values[j] = values[j - 1];
            --j;
        }
        values[j] = key;
    }
}
```

불변식:

```text
외부 반복 i가 시작될 때 values[0..i)는 정렬되어 있고,
원래 values[0..i)의 같은 원소들을 포함한다.
```

증명 구조:

- 초기화: i=1일 때 길이 1 구간은 정렬됨
- 유지: key를 올바른 위치에 삽입하면 정렬과 원소 보존
- 종료: i=n이면 전체가 정렬됨

## 25.4 종료 증명

반복이 끝나는 이유를 variant로 설명한다. 위 내부 루프에서 `j`는 음수가 되지 않는 자연수이며 반복마다 감소한다.

무한 루프 버그를 줄이려면 “무엇이 단조롭게 목표에 가까워지는가?”를 찾는다.

## 25.5 재귀식

병합 정렬:

```text
T(n) = 2T(n/2) + Θ(n) = Θ(n log n)
```

분할 정복을 사용할 때 다음을 본다.

- 부분 문제 수
- 부분 문제 크기
- 분할·결합 비용
- recursion overhead
- 추가 메모리
- 병렬 가능성

## 25.6 상환 분석

`std::vector::push_back`은 재할당 때 O(n)이지만 capacity를 기하급수적으로 늘리면 긴 연산열의 평균 비용은 상환 O(1)이다. 단, 특정 한 번의 지연은 O(n)이므로 hard real-time 경로에서는 문제가 될 수 있다.

<div class="exercise">

### 25장 연습

1. binary search의 불변식과 종료 조건을 작성하라.
2. 재귀 DFS가 stack overflow를 일으키는 입력을 만들고 iterative 버전으로 바꾸라.
3. `vector` growth factor가 2와 1.5일 때 재할당·낭비 메모리를 비교하라.
4. 평균 O(1)과 worst-case O(n)의 차이가 보안 문제로 이어지는 예를 설명하라.
5. 게임 프레임에서 상환 비용이 위험한 이유를 설명하라.

</div>

# 26장. 배열, 리스트, 해시, 트리

## 26.1 배열과 벡터

장점:

- 연속 메모리
- O(1) index
- 우수한 cache locality
- SIMD와 bulk operation에 유리

단점:

- 중간 삽입·삭제 이동 비용
- 재할당으로 포인터·반복자 무효화
- 안정 주소가 필요한 경우 제약

```cpp
std::vector<Enemy> enemies;
enemies.reserve(expectedCount);
```

`reserve`는 재할당 빈도를 줄이지만, 예상보다 커지면 다시 재할당된다. 포인터 안정성을 보장하는 계약이 아니다.

## 26.2 연결 리스트

이론적 O(1) 삽입·삭제는 해당 노드를 이미 알고 있을 때다. 노드 검색, 할당, 포인터 추적, 캐시 미스가 비용이다.

사용 적합 사례:

- 안정 iterator가 중요하고
- 이동할 수 없는 객체가 많고
- 알려진 위치에서 잦은 splice가 있으며
- 실제 측정이 이점을 보일 때

## 26.3 해시 테이블

구성 요소:

- hash function
- bucket/index 계산
- collision resolution
- load factor
- resize 정책

### separate chaining

각 bucket에 리스트/벡터를 둔다.

### open addressing

배열 내부에서 probe한다.

- linear probing
- quadratic probing
- double hashing
- Robin Hood hashing

open addressing은 locality가 좋을 수 있지만 삭제 marker와 높은 load에서 probe가 길어진다.

## 26.4 해시 품질와 공격

비신뢰 입력이 같은 bucket으로 몰리면 성능이 악화될 수 있다. 웹 프레임워크와 파서는 hash-flooding을 고려해야 한다.

해시는 목적에 따라 다르다.

- 일반 컨테이너용 빠른 hash
- cryptographic hash
- checksum
- consistent hash

서로 대체할 수 없다.

## 26.5 binary search tree

BST 불변식:

```text
왼쪽 subtree의 모든 key < node.key
오른쪽 subtree의 모든 key > node.key
```

균형이 없으면 정렬 입력에서 연결 리스트처럼 O(n)이 된다. Red-Black, AVL 등 균형 트리는 높이를 O(log n)으로 제한한다.

## 26.6 B-tree와 저장장치

B-tree는 노드 하나에 여러 key와 child를 담아 tree 높이와 I/O 횟수를 줄인다. 디스크·페이지 단위 접근에 맞춘 구조다.

```text
[10 | 20 | 35]
 /    |    |    \
<10 10..20 20..35 >35
```

CPU cache와 SSD page에서도 node fanout과 layout이 중요하다.

## 26.7 trie

문자열 prefix를 edge로 표현한다. 자동완성, routing, dictionary에 유용하지만 pointer-heavy 구현은 메모리를 많이 사용한다. compressed trie/radix tree를 고려한다.

# 27장. 정렬, 선택, 검색

## 27.1 정렬 알고리즘을 조건으로 선택한다

| 알고리즘 | 평균 | 최악 | 안정성 | 추가 메모리 | 특징 |
|---|---:|---:|---|---:|---|
| insertion | n² | n² | 안정 | O(1) | 작은/거의 정렬 데이터 |
| merge | n log n | n log n | 안정 가능 | O(n) | sequential access |
| quicksort | n log n | n² | 불안정 | O(log n) stack | cache-friendly |
| heapsort | n log n | n log n | 불안정 | O(1) | worst-case 보장 |
| radix | 조건부 선형 | 조건부 | 구현에 따라 | 추가 버퍼 | fixed-width key |

표준 라이브러리는 일반적으로 고도로 최적화되어 있다. 직접 정렬을 작성하는 목적은 학습과 특수 제약이지, 습관적으로 대체하는 것이 아니다.

## 27.2 비교 정렬의 하한

서로 다른 n개 원소의 가능한 순서는 n!개다. 비교 한 번은 의사결정 트리에서 두 갈래를 구분한다. 모든 순서를 구분하려면 깊이가 최소 `log₂(n!) = Ω(n log n)`이다.

radix sort가 이 하한을 피하는 이유는 단순 비교 모델이 아니라 key의 숫자 구조를 이용하기 때문이다.

## 27.3 binary search의 경계 버그

```cpp
std::optional<std::size_t> lower_bound_index(std::span<const int> a, int target) {
    std::size_t first = 0;
    std::size_t last = a.size(); // half-open [first,last)

    while (first < last) {
        const std::size_t mid = first + (last - first) / 2;
        if (a[mid] < target) first = mid + 1;
        else last = mid;
    }

    if (first < a.size() && a[first] == target) return first;
    return std::nullopt;
}
```

half-open range는 empty range와 길이 계산이 단순하다.

## 27.4 selection

k번째 작은 원소가 필요할 때 전체 정렬 O(n log n)이 과하다. Quickselect는 평균 O(n), median-of-medians는 최악 O(n) 보장이 가능하지만 상수와 구현 복잡성이 다르다.

## 27.5 문자열 검색

naive search는 최악 O(nm). KMP는 pattern의 prefix 정보를 이용해 이미 비교한 문자를 다시 보지 않아 O(n+m)을 달성한다. Boyer-Moore 계열은 뒤에서 비교하고 큰 skip을 사용해 실전에서 강할 수 있다.

문자열은 byte sequence인지 Unicode code point인지 grapheme cluster인지 구분해야 한다. 사용자에게 보이는 “문자 수”와 UTF-8 byte 수는 다르다.

# 28장. 그래프 알고리즘과 상태 공간

## 28.1 그래프 모델링

그래프는 정점과 간선으로 관계를 표현한다.

- 게임 맵과 이동 경로
- 빌드 의존성
- call graph
- 소셜 관계
- 네트워크 topology
- 상태 전이

모델링이 알고리즘보다 중요할 때가 많다. 간선이 방향성인지, 가중치가 음수인지, 동적으로 변하는지 정해야 한다.

## 28.2 BFS와 DFS

BFS는 unweighted graph의 최소 edge 수 경로를 찾는다.

```cpp
std::vector<int> bfs_dist(const Graph& g, int source) {
    std::vector<int> dist(g.size(), -1);
    std::queue<int> q;
    dist[source] = 0;
    q.push(source);
    while (!q.empty()) {
        const int u = q.front(); q.pop();
        for (int v : g[u]) {
            if (dist[v] == -1) {
                dist[v] = dist[u] + 1;
                q.push(v);
            }
        }
    }
    return dist;
}
```

DFS는 cycle detection, topological sort, component 탐색에 사용된다.

## 28.3 Dijkstra

non-negative edge weight의 shortest path.

핵심 불변식:

```text
priority queue에서 확정한 최소 거리 정점은 이후 더 짧아지지 않는다.
```

음수 edge가 있으면 이 불변식이 깨진다. Bellman-Ford 같은 다른 알고리즘이 필요하다.

## 28.4 A*와 heuristic

```text
f(n) = g(n) + h(n)
```

- g: 시작부터 현재까지 실제 비용
- h: 목표까지 추정 비용

heuristic이 admissible하면 최적 경로 보장에 도움이 된다. consistent하면 closed node 재개방을 줄일 수 있다.

게임에서는 완전 최적보다 시간 budget, path smoothing, dynamic obstacle 대응이 중요할 수 있다.

## 28.5 topological sort

DAG의 의존 순서를 구한다. 빌드 시스템과 render graph에 사용된다.

Kahn algorithm:

```text
indegree 0 node를 queue에 넣음
→ 제거하며 outgoing neighbor indegree 감소
→ 새로 0이 된 node 추가
→ 처리 수가 전체보다 작으면 cycle
```

## 28.6 union-find

disjoint set을 관리한다. path compression + union by rank로 실질적으로 매우 빠르다.

응용:

- Kruskal MST
- 연결성 질의
- 이미지 component labeling
- network grouping

# 29장. 확률적 자료 구조와 무작위 알고리즘

## 29.1 무작위성은 포기가 아니라 도구다

무작위 알고리즘은 기대 성능, 단순성, 공격 회피에 도움을 준다. 하지만 재현 가능한 테스트를 위해 seed를 기록한다.

```cpp
std::mt19937 rng(seed);
```

`std::random_device`의 성질은 구현에 따라 다를 수 있고 cryptographic randomness와 동일하게 생각하면 안 된다.

## 29.2 Bloom filter

bit array와 여러 hash function으로 set membership을 근사한다.

- false negative 없음: 넣은 것은 있다고 답함
- false positive 가능: 안 넣은 것을 있다고 답할 수 있음

DB/캐시에서 비싼 lookup을 피하기 위한 전단 filter로 사용한다.

## 29.3 reservoir sampling

길이를 미리 모르는 stream에서 k개 균등 sample을 유지한다.

k=1:

```cpp
std::optional<Value> sample;
std::uint64_t seen = 0;
for (Value v : stream) {
    ++seen;
    std::uniform_int_distribution<std::uint64_t> d(1, seen);
    if (d(rng) == 1) sample = v;
}
```

## 29.4 randomized quicksort

pivot을 무작위 선택하면 특정 입력 순서가 반복적으로 worst-case를 만드는 위험을 줄인다. 보안 공격자가 seed나 hash를 예측할 수 있는 상황은 별도 고려한다.

## 29.5 approximate counting와 sketches

대규모 stream에서 모든 원소를 저장하지 않고 빈도·distinct count를 추정한다. 오차 범위와 confidence를 결과 일부로 다룬다.

# 30장. 알고리즘을 실제 시스템에 맞추기

## 30.1 cache-aware와 cache-oblivious

이론적 연산 수가 같아도 메모리 접근이 다르면 성능이 크게 달라진다. matrix multiplication의 loop 순서와 blocking은 cache reuse를 만든다.

```cpp
for (std::size_t ii = 0; ii < n; ii += B)
  for (std::size_t kk = 0; kk < n; kk += B)
    for (std::size_t jj = 0; jj < n; jj += B)
      for (std::size_t i = ii; i < std::min(ii+B,n); ++i)
        for (std::size_t k = kk; k < std::min(kk+B,n); ++k)
          for (std::size_t j = jj; j < std::min(jj+B,n); ++j)
            C[i*n+j] += A[i*n+k] * Bm[k*n+j];
```

block size는 cache와 element size에 따라 측정한다.

## 30.2 external-memory algorithm

데이터가 RAM보다 크면 disk I/O가 중심 비용이다.

- sequential scan
- external merge sort
- B-tree
- LSM tree
- chunk와 streaming

모든 데이터를 vector에 읽은 뒤 처리하는 습관을 버려야 한다.

## 30.3 online algorithm

미래 입력을 모르는 상태에서 결정을 내린다. cache replacement, scheduling, matchmaking에 등장한다. offline optimal과 경쟁 비율을 비교할 수 있다.

## 30.4 parallel algorithm

병렬화 전에 work와 span을 구분한다.

- work: 전체 연산량
- span: 무한 processor에서도 남는 critical path

Amdahl의 법칙은 직렬 부분이 speedup을 제한한다. [[Amdahl 1967](https://www3.cs.stonybrook.edu/~rezaul/Spring-2012/CSE613/reading/Amdahl-1967.pdf)]

```text
speedup = 1 / (serial_fraction + parallel_fraction / processors)
```

오버헤드, load imbalance, memory bandwidth 때문에 실제는 더 낮다.

## 30.5 backpressure

생산자가 소비자보다 빠르면 queue가 무한히 자란다. 알고리즘은 처리량뿐 아니라 흐름 제어를 포함해야 한다.

정책:

- producer block
- drop newest/oldest
- batch
- adaptive sampling
- upstream rate limit
- spill to disk

게임 telemetry, network packet, asset streaming에서 어떤 데이터를 잃어도 되는지 도메인 결정이 필요하다.

## 30.6 정확도와 비용의 교환

- 근사 pathfinding
- level of detail
- probabilistic filter
- lossy compression
- approximate query

최적화는 결과 품질의 허용 범위를 명시할 때 가능하다.

<div class="check">

### 제5부 통과 기준

- 알고리즘의 불변식·종료·복잡도를 구분해 설명한다.
- 같은 O(n) 알고리즘이 cache 때문에 크게 달라지는 실험을 수행한다.
- hash table의 평균과 최악 조건을 설명한다.
- Dijkstra와 A*의 전제 조건을 말한다.
- 데이터가 RAM보다 클 때 설계를 바꿀 수 있다.
- backpressure 정책을 도메인 요구로 선택한다.

</div>
