from __future__ import annotations

from pathlib import Path
import platform
import subprocess
import tempfile
import unittest

from x64_codegen import Parser, X64Emitter, execute, write_elf64


@unittest.skipUnless(platform.machine().lower() in {"x86_64", "amd64"}, "x86-64 host required")
class MachineCodeTests(unittest.TestCase):
    def evaluate(self, source: str) -> int:
        tree = Parser(source).parse()
        code = X64Emitter().emit_function(tree)
        return execute(code)

    def test_arithmetic(self) -> None:
        cases = {
            "2 + 3 * 4": 14,
            "(20 - 3) * -2": -34,
            "-17 / 5": -3,
            "-17 % 5": -2,
            "0x10 + 0b11": 19,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(self.evaluate(source), expected)

    @unittest.skipUnless(platform.system() == "Linux", "ELF test requires Linux")
    def test_minimal_elf_exit_status(self) -> None:
        tree = Parser("40 + 2").parse()
        code = X64Emitter().emit_process_entry(tree)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "answer"
            write_elf64(path, code)
            completed = subprocess.run([str(path)], check=False)
            self.assertEqual(completed.returncode, 42)


if __name__ == "__main__":
    unittest.main()
