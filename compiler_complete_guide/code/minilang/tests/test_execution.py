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
