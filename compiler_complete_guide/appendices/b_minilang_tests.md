# 부록 B. MiniLang 예제와 테스트

실행 예제, frontend/execution 회귀 테스트, 패키지 메타데이터.
수록 파일 9개, 약 393줄.


이 부록의 코드는 본문에서 사용한 검증 원본이다. 줄 번호는 편집·수정에 따라 바뀔 수 있으므로 클래스·함수 이름으로 찾아간다.

## `code/minilang/tests/test_execution.py`

`````python
from __future__ import annotations

from io import StringIO
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

from minilang.driver import compile_source
from minilang.interpreter import Interpreter, MiniLangRuntimeError
from minilang.llvm_backend import LLVMBackend


class InterpreterTests(unittest.TestCase):
    def run_source(self, source: str, optimize: bool = False) -> tuple[int, str]:
        unit = compile_source(source, optimize=optimize)
        self.assertTrue(unit.succeeded, unit.diagnostics)
        output = StringIO()
        result = Interpreter(unit.program, unit.analysis, output).run()
        return result, output.getvalue()

    def test_functions_loops_arrays_and_structs(self) -> None:
        source = """
        struct Pair { left: int; right: int; }
        fn sum(xs: [int; 4]) -> int {
            let result: int = 0;
            for (let i: int = 0; i < len(xs); i = i + 1) {
                result = result + xs[i];
            }
            return result;
        }
        fn main() -> int {
            let xs: [int; 4] = [1, 2, 3, 4];
            let pair: Pair = Pair { left: 10, right: 20 };
            xs[2] = pair.left;
            pair.right = 5;
            let value: int = sum(xs) + pair.right;
            print_int(value);
            return value;
        }
        """
        result, output = self.run_source(source)
        self.assertEqual(result, 22)
        self.assertEqual(output, "22\n")

    def test_recursion(self) -> None:
        source = """
        fn factorial(n: int) -> int {
            if (n <= 1) { return 1; }
            return n * factorial(n - 1);
        }
        fn main() -> int { return factorial(10); }
        """
        result, _ = self.run_source(source)
        self.assertEqual(result, 3628800)

    def test_short_circuit(self) -> None:
        source = """
        fn main() -> int {
            let x: int = 0;
            if (false && ((x = 1) == 1)) { x = 2; }
            if (true || ((x = 3) == 3)) { x = x + 4; }
            return x;
        }
        """
        result, _ = self.run_source(source)
        self.assertEqual(result, 4)

    def test_runtime_bounds_check(self) -> None:
        source = "fn main() -> int { let xs: [int; 1] = [7]; return xs[2]; }"
        unit = compile_source(source)
        self.assertTrue(unit.succeeded)
        with self.assertRaisesRegex(MiniLangRuntimeError, "out of bounds"):
            Interpreter(unit.program, unit.analysis).run()

    def test_optimizer_preserves_result(self) -> None:
        source = """
        fn main() -> int {
            let x: int = (2 + 3) * 4;
            if (true) { return x; } else { return 99; }
            return 100;
        }
        """
        plain, _ = self.run_source(source, optimize=False)
        optimized, _ = self.run_source(source, optimize=True)
        self.assertEqual(plain, optimized)
        unit = compile_source(source, optimize=True)
        self.assertGreaterEqual(unit.optimization_stats.constants_folded, 2)
        self.assertGreaterEqual(unit.optimization_stats.branches_removed, 1)
        self.assertGreaterEqual(unit.optimization_stats.statements_removed, 1)


@unittest.skipUnless(shutil.which("clang"), "clang is required for LLVM integration tests")
class LLVMBackendTests(unittest.TestCase):
    def compile_and_run(self, source: str) -> subprocess.CompletedProcess[str]:
        unit = compile_source(source)
        self.assertTrue(unit.succeeded, unit.diagnostics)
        llvm = LLVMBackend(unit.program, unit.analysis, "test_module").emit()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ll_path = root / "program.ll"
            executable = root / "program"
            ll_path.write_text(llvm, encoding="utf-8")
            compile_process = subprocess.run(
                [shutil.which("clang"), str(ll_path), "-o", str(executable)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(compile_process.returncode, 0, compile_process.stderr + "\n" + llvm)
            return subprocess.run([str(executable)], text=True, capture_output=True, check=False)

    def test_native_arrays_structs_calls_and_control_flow(self) -> None:
        source = """
        struct Point { x: int; y: int; }
        fn dot(a: Point, b: Point) -> int { return a.x * b.x + a.y * b.y; }
        fn main() -> int {
            let xs: [int; 3] = [1, 2, 3];
            let a: Point = Point { x: xs[0], y: xs[1] };
            let b: Point = Point { x: 4, y: 5 };
            let total: int = 0;
            for (let i: int = 0; i < len(xs); i = i + 1) { total = total + xs[i]; }
            print_int(dot(a, b) + total);
            return 0;
        }
        """
        process = self.compile_and_run(source)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout, "20\n")

    def test_strings_and_short_circuit(self) -> None:
        source = """
        fn main() -> int {
            let text: string = "compiler";
            print_string(text);
            print_int(len(text));
            print_bool((text == "compiler") && true);
            return 0;
        }
        """
        process = self.compile_and_run(source)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout, "compiler\n8\ntrue\n")

    def test_randomized_expression_differential(self) -> None:
        rng = random.Random(20260324)
        operators = ["+", "-", "*"]
        for _ in range(12):
            values = [rng.randint(-20, 20) for _ in range(7)]
            expression = str(values[0])
            for value in values[1:]:
                expression = f"({expression} {rng.choice(operators)} {value})"
            source = f"fn main() -> int {{ print_int({expression}); return 0; }}"
            unit = compile_source(source)
            self.assertTrue(unit.succeeded, unit.diagnostics)
            expected_output = StringIO()
            Interpreter(unit.program, unit.analysis, expected_output).run()
            process = self.compile_and_run(source)
            self.assertEqual(process.stdout, expected_output.getvalue())


if __name__ == "__main__":
    unittest.main()
`````

## `code/minilang/tests/test_frontend.py`

`````python
from __future__ import annotations

import unittest

from minilang import ast
from minilang.ast_dump import dump
from minilang.driver import compile_source
from minilang.lexer import Lexer
from minilang.parser import Parser
from minilang.token import TokenKind


class LexerTests(unittest.TestCase):
    def test_keywords_identifiers_and_locations(self) -> None:
        source = "let 변수 = 0x2a + 0b10;\nreturn 변수;"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertFalse(lexer.diagnostics.has_errors)
        self.assertEqual(tokens[0].kind, TokenKind.LET)
        self.assertEqual(tokens[1].lexeme, "변수")
        self.assertEqual(tokens[3].literal, 42)
        self.assertEqual(tokens[5].literal, 2)
        self.assertEqual(tokens[7].span.start.line, 2)

    def test_nested_comments_and_string_escapes(self) -> None:
        source = '/* outer /* inner */ done */ "a\\n\\u{41}"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertFalse(lexer.diagnostics.has_errors)
        self.assertEqual(tokens[0].kind, TokenKind.STRING)
        self.assertEqual(tokens[0].literal, "a\nA")

    def test_invalid_input_produces_recoverable_tokens(self) -> None:
        lexer = Lexer('"unterminated\n@')
        tokens = lexer.tokenize()
        self.assertTrue(lexer.diagnostics.has_errors)
        self.assertEqual(tokens[0].kind, TokenKind.ERROR)
        self.assertEqual(tokens[1].kind, TokenKind.ERROR)
        self.assertEqual(tokens[-1].kind, TokenKind.EOF)


class ParserTests(unittest.TestCase):
    def parse(self, source: str) -> ast.Program:
        lexer = Lexer(source)
        parser = Parser(lexer.tokenize())
        program = parser.parse_program()
        self.assertFalse(lexer.diagnostics.has_errors, lexer.diagnostics.items)
        self.assertFalse(parser.diagnostics.has_errors, parser.diagnostics.items)
        return program

    def test_precedence(self) -> None:
        program = self.parse("fn main() -> int { return 1 + 2 * 3 == 7 || false; }")
        function = program.declarations[0]
        self.assertIsInstance(function, ast.FunctionDecl)
        return_stmt = function.body.statements[0]
        self.assertIsInstance(return_stmt, ast.ReturnStmt)
        expression = return_stmt.value
        self.assertIsInstance(expression, ast.BinaryExpr)
        self.assertEqual(expression.operator, "||")
        self.assertIsInstance(expression.left, ast.BinaryExpr)
        self.assertEqual(expression.left.operator, "==")

    def test_all_statement_forms(self) -> None:
        source = """
        fn main() -> int {
            let x: int = 0;
            while (x < 3) { x = x + 1; }
            for (let i: int = 0; i < 2; i = i + 1) { x = x + i; }
            if (x > 0) { return x; } else { return 0; }
        }
        """
        program = self.parse(source)
        function = program.declarations[0]
        self.assertEqual(len(function.body.statements), 4)
        self.assertIsInstance(function.body.statements[1], ast.WhileStmt)
        self.assertIsInstance(function.body.statements[2], ast.ForStmt)
        self.assertIsInstance(function.body.statements[3], ast.IfStmt)

    def test_ast_dump_is_deterministic(self) -> None:
        program = self.parse("fn main() -> int { return 42; }")
        text = dump(program)
        self.assertIn("Program", text)
        self.assertIn("IntegerExpr", text)
        self.assertNotIn("SourceSpan", text)


class SemanticTests(unittest.TestCase):
    def test_valid_program(self) -> None:
        source = """
        struct P { x: int; y: int; }
        fn length2(p: P) -> int { return p.x * p.x + p.y * p.y; }
        fn main() -> int {
            let p: P = P { x: 3, y: 4 };
            let xs: [int; 2] = [length2(p), 1];
            return xs[0];
        }
        """
        unit = compile_source(source)
        self.assertTrue(unit.succeeded, unit.diagnostics)

    def test_reports_multiple_errors(self) -> None:
        source = """
        struct P { x: int; }
        fn main() -> int {
            let p: P = P { y: 1 };
            let b: bool = 3;
            unknown = b + 1;
            return "bad";
        }
        """
        unit = compile_source(source)
        codes = {diagnostic.code for diagnostic in unit.diagnostics}
        self.assertGreaterEqual(len(unit.diagnostics), 5)
        self.assertIn("SEM020", codes)
        self.assertIn("SEM022", codes)
        self.assertIn("SEM011", codes)
        self.assertIn("SEM014", codes)
        self.assertIn("SEM013", codes)

    def test_scope_shadowing_is_legal_but_same_scope_duplicate_is_not(self) -> None:
        valid = compile_source("fn main() -> int { let x: int = 1; { let x: int = 2; } return x; }")
        self.assertTrue(valid.succeeded, valid.diagnostics)
        invalid = compile_source("fn main() -> int { let x: int = 1; let x: int = 2; return x; }")
        self.assertIn("SEM012", {diagnostic.code for diagnostic in invalid.diagnostics})


if __name__ == "__main__":
    unittest.main()
`````

## `code/minilang/examples/arrays_structs.mini`

`````text
struct Point {
    x: int;
    y: int;
}

fn dot(a: Point, b: Point) -> int {
    return a.x * b.x + a.y * b.y;
}

fn sum(values: [int; 5]) -> int {
    let total: int = 0;
    for (let i: int = 0; i < len(values); i = i + 1) {
        total = total + values[i];
    }
    return total;
}

fn main() -> int {
    let values: [int; 5] = [2, 3, 5, 7, 11];
    let left: Point = Point { x: 2, y: 3 };
    let right: Point = Point { x: 5, y: 7 };

    values[0] = values[0] + 1;
    left.x = 4;

    print_int(sum(values));
    print_int(dot(left, right));
    return 0;
}
`````

## `code/minilang/examples/control_flow.mini`

`````text
fn gcd(a0: int, b0: int) -> int {
    let a: int = a0;
    let b: int = b0;
    while (b != 0) {
        let remainder: int = a % b;
        a = b;
        b = remainder;
    }
    return a;
}

fn main() -> int {
    let answer: int = gcd(1071, 462);
    assert(answer == 21);
    print_int(answer);
    return 0;
}
`````

## `code/minilang/examples/diagnostics.mini`

`````text
struct Pair {
    left: int;
    right: int;
}

fn main() -> int {
    let pair: Pair = Pair { left: 1 };
    let count: bool = 42;
    missing = count + 1;
    return "not an integer";
}
`````

## `code/minilang/examples/fibonacci.mini`

`````text
fn fib(n: int) -> int {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

fn main() -> int {
    let value: int = fib(10);
    print_int(value);
    return 0;
}
`````

## `code/minilang/examples/hello.mini`

`````text
fn main() -> int {
    print_string("Hello, MiniLang!");
    return 0;
}
`````

## `code/minilang/examples/optimization.mini`

`````text
fn main() -> int {
    let folded: int = (2 + 3) * (10 - 4);
    if (true && (folded == 30)) {
        print_int(folded);
        return 0;
        print_string("dead");
    } else {
        return 1;
    }
}
`````

## `code/minilang/pyproject.toml`

`````toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "minilang-compiler-book"
version = "1.0.0"
description = "Executable teaching compiler accompanying 프로그래머를 위한 컴파일러 완전 정복"
requires-python = ">=3.11"
authors = [{name = "Compiler Book Project"}]
license = {text = "MIT"}

[project.scripts]
minilang = "minilang.cli:main"

[tool.setuptools]
packages = ["minilang"]
`````
