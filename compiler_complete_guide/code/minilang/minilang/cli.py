"""Command-line interface for the MiniLang teaching compiler."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .ast_dump import dump
from .diagnostics import render_diagnostic
from .driver import CompilationUnit, compile_source
from .interpreter import Interpreter, MiniLangRuntimeError
from .llvm_backend import CodegenError, LLVMBackend


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="minilang", description="MiniLang teaching compiler")
    parser.add_argument("--version", action="version", version="MiniLang 1.0.0")
    subcommands = parser.add_subparsers(dest="command", required=True)

    def source_command(name: str, help_text: str) -> argparse.ArgumentParser:
        command = subcommands.add_parser(name, help=help_text)
        command.add_argument("source", type=Path)
        command.add_argument("-O", "--optimize", action="store_true")
        return command

    source_command("tokens", "print the token stream")
    source_command("ast", "print the abstract syntax tree")
    source_command("check", "parse and type-check a source file")
    source_command("run", "execute with the reference interpreter")

    llvm = source_command("emit-llvm", "emit LLVM IR")
    llvm.add_argument("-o", "--output", type=Path)

    build = source_command("build", "emit LLVM IR and invoke clang")
    build.add_argument("-o", "--output", type=Path, required=True)
    build.add_argument("--clang", default=os.environ.get("CLANG", "clang"))
    build.add_argument("--clang-arg", action="append", default=[])
    return parser


def _load(path: Path, optimize: bool) -> CompilationUnit:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"minilang: cannot read {path}: {exc}") from exc
    unit = compile_source(source, optimize=optimize)
    if unit.diagnostics:
        for diagnostic in unit.diagnostics:
            print(render_diagnostic(str(path), source, diagnostic), file=sys.stderr)
        raise SystemExit(1)
    return unit


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    unit = _load(args.source, args.optimize)

    if args.command == "tokens":
        for token in unit.tokens:
            print(token)
        return 0
    if args.command == "ast":
        print(dump(unit.program))
        return 0
    if args.command == "check":
        print(f"OK: {args.source}")
        if unit.optimization_stats is not None:
            stats = unit.optimization_stats
            print(
                f"optimized: folded={stats.constants_folded}, "
                f"branches={stats.branches_removed}, dead-statements={stats.statements_removed}"
            )
        return 0
    if args.command == "run":
        try:
            exit_code = Interpreter(unit.program, unit.analysis, sys.stdout).run()
        except MiniLangRuntimeError as exc:
            print(f"runtime error: {exc}", file=sys.stderr)
            return 70
        return exit_code & 0xFF

    try:
        llvm = LLVMBackend(unit.program, unit.analysis, args.source.stem).emit()
    except CodegenError as exc:
        print(f"code generation error: {exc}", file=sys.stderr)
        return 1

    if args.command == "emit-llvm":
        if args.output:
            args.output.write_text(llvm, encoding="utf-8")
        else:
            sys.stdout.write(llvm)
        return 0

    if args.command == "build":
        clang = shutil.which(args.clang)
        if clang is None:
            print(f"minilang: clang executable not found: {args.clang}", file=sys.stderr)
            return 1
        llvm_path = args.output.with_suffix(args.output.suffix + ".ll")
        llvm_path.write_text(llvm, encoding="utf-8")
        command = [clang, str(llvm_path), "-o", str(args.output), *args.clang_arg]
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
        print(args.output)
        return 0

    raise AssertionError(f"unknown command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
