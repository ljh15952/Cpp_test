# 프로그래머를 위한 컴파일러 완전 정복 — 출판 프로젝트

부제: **이론부터 구현까지 따라 하며 배우는 컴파일러 제작**

이 저장소는 EPUB 원고, 장별 Markdown, 참고문헌, 용어집, 색인, 자동 빌드 스크립트와 실행 가능한 컴파일러 실습 코드를 포함한다.

## 구성

- 15개 Part, 67개 본문 장
- 4개 앞부분 문서, 15개 Part 안내, 5개 전체 소스 부록, 용어집·색인
- EPUB 스파인 입력 Markdown 93개
- C11 Lexer
- Rust 2021 Lexer
- C++20 AST Visitor
- Go Pratt Parser
- Python MiniLang 전체 파이프라인
- 지배·SSA·활성·linear-scan 최적화 연구실
- LLVM IR/API/다중 ISA 예제
- 직접 x86-64 instruction bytes 및 최소 ELF64 생성기

## MiniLang 기능

- 변수와 어휘 scope
- 함수와 재귀
- `if`, `while`, C형 `for`, `return`
- 고정 길이 배열
- UTF-8 문자열
- 구조체와 필드 접근
- 타입 검사, 다중 진단, 배열 경계와 0 나눗셈 검사
- 참조 인터프리터, AST 최적화, LLVM IR 백엔드, native build

## 빠른 검증

```bash
./scripts/verify.sh
```

이 명령은 원고 재생성·정적 검사, Python/C/C++/Go 테스트, LLVM 다중 target 생성, llvmlite JIT, EPUB 빌드와 EPUB 내부 링크 검사를 실행한다. Rust 도구체인이 있으면 `cargo test`도 실행하며, 없으면 보고서에 `SKIP`으로 기록한다.

## EPUB 빌드

```bash
./scripts/build_epub.sh build/programmer_compiler_complete_guide.epub
python3 scripts/validate_epub.py build/programmer_compiler_complete_guide.epub
```

필수 도구는 Pandoc 3 계열, Python 3, zip/unzip이다. 코드 전체 검증에는 Clang, C11/C++20 컴파일러, Go가 필요하다.

## Markdown 구조

- `front/`: 표제, 머리말, 사용법, 프로젝트 로드맵
- `chapters/`: Part 안내와 67개 독립 장
- `appendices/`: 전체 검증 소스 전문
- `back/`: 용어집과 색인
- `TOC.md`: Markdown 탐색 목차
- `book_order.txt`: EPUB 입력 순서
- `references.bib`: 논문·교재·공식 문서 참고문헌

모든 본문 장은 다음 순서를 따른다.

1. 학습 목표
2. 이론
3. 배경지식
4. 그림(ASCII Diagram)
5. 실제 예제
6. 코드 설명
7. 따라하기 실습
8. 실습 결과
9. 자주 발생하는 오류
10. 해결 방법
11. 요약
12. 연습 문제
13. 심화 과제
14. 참고 논문
15. 참고 문헌

`따라하기 실습`에는 따라 하기, 실습, 결과 확인, 체크리스트, 복습, 퀴즈, 응용 예제, 프로젝트가 포함된다.

## 검증 상태

- MiniLang Python 테스트: 17개
- 최적화 연구실 테스트: 3개
- 직접 기계어 생성기 테스트: 2개
- C11 Lexer: 경고를 오류로 처리한 빌드와 회귀 검사
- C++20 Visitor: 경고를 오류로 처리한 빌드와 실행 검사
- Go Pratt Parser: `go test ./...`
- LLVM: O0/O2 IR, x86, x86-64, AArch64, RISC-V assembly, native exit 42
- llvmlite API/JIT: result 42
- EPUB: ZIP, mimetype, OPF, manifest, spine, nav, cover, XHTML, 내부 링크 검사

현재 빌드 환경에는 Rust 도구체인이 없으므로 Rust 2021 소스는 표준 라이브러리 전용 코드와 단위 테스트를 포함하되 실행 검증은 수행하지 않았다.

## 분량

`reports/metrics.md`에 실제 문자·코드 줄 수와 페이지 환산식을 기록한다. EPUB은 reflow 형식이므로 고정 페이지 수가 없으며, 현재 원고의 인쇄 환산 중앙 추정치는 약 1,000쪽이다.
