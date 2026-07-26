# 부록 A. MiniLang 컴파일러 핵심 소스

Lexer부터 LLVM backend와 CLI까지의 Python 핵심 구현.
수록 파일 16개, 약 3,223줄.


이 부록의 코드는 본문에서 사용한 검증 원본이다. 줄 번호는 편집·수정에 따라 바뀔 수 있으므로 클래스·함수 이름으로 찾아간다.

## `code/minilang/minilang/__init__.py`

`````python
"""MiniLang teaching compiler package."""

__version__ = "1.0.0"
`````

## `code/minilang/minilang/__main__.py`

`````python
from .cli import main

raise SystemExit(main())
`````

## `code/minilang/minilang/ast.py`

`````python
"""Abstract syntax tree nodes for MiniLang.

Nodes are intentionally small data objects. Semantic facts such as resolved
symbols and inferred types live in side tables, which keeps parsing independent
from name resolution and permits multiple analyses over the same tree.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .token import SourceSpan


@dataclass(frozen=True, slots=True)
class TypeSyntax:
    span: SourceSpan
    name: str | None = None
    element: "TypeSyntax | None" = None
    length: int | None = None

    def display(self) -> str:
        if self.element is not None:
            return f"[{self.element.display()}; {self.length}]"
        return self.name or "<missing-type>"


class Node:
    span: SourceSpan


class Expr(Node):
    pass


class Stmt(Node):
    pass


class Decl(Node):
    pass


@dataclass(frozen=True, slots=True)
class Program(Node):
    declarations: tuple[Decl, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class StructField:
    name: str
    type_syntax: TypeSyntax
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class StructDecl(Decl):
    name: str
    fields: tuple[StructField, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class Parameter:
    name: str
    type_syntax: TypeSyntax
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class FunctionDecl(Decl):
    name: str
    parameters: tuple[Parameter, ...]
    return_type: TypeSyntax
    body: "BlockStmt"
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class BlockStmt(Stmt):
    statements: tuple[Stmt, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class LetStmt(Stmt):
    name: str
    type_syntax: TypeSyntax | None
    initializer: Expr
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ExprStmt(Stmt):
    expression: Expr
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class IfStmt(Stmt):
    condition: Expr
    then_branch: BlockStmt
    else_branch: BlockStmt | "IfStmt" | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class WhileStmt(Stmt):
    condition: Expr
    body: BlockStmt
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ForStmt(Stmt):
    initializer: Stmt | None
    condition: Expr | None
    increment: Expr | None
    body: BlockStmt
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ReturnStmt(Stmt):
    value: Expr | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class AssignExpr(Expr):
    target: Expr
    value: Expr
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class BinaryExpr(Expr):
    left: Expr
    operator: str
    right: Expr
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class UnaryExpr(Expr):
    operator: str
    operand: Expr
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class CallExpr(Expr):
    callee: Expr
    arguments: tuple[Expr, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class IndexExpr(Expr):
    collection: Expr
    index: Expr
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class FieldExpr(Expr):
    receiver: Expr
    name: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class NameExpr(Expr):
    name: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class IntegerExpr(Expr):
    value: int
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class BooleanExpr(Expr):
    value: bool
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class StringExpr(Expr):
    value: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ArrayExpr(Expr):
    elements: tuple[Expr, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class StructInitField:
    name: str
    value: Expr
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class StructInitExpr(Expr):
    name: str
    fields: tuple[StructInitField, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ErrorExpr(Expr):
    span: SourceSpan
    message: str = field(default="invalid expression")
`````

## `code/minilang/minilang/ast_dump.py`

`````python
"""Deterministic text rendering of the MiniLang AST for tests and diagnostics."""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum

from .token import SourcePosition, SourceSpan


def dump(node: object) -> str:
    lines: list[str] = []
    _visit(node, lines, "", "")
    return "\n".join(lines)


def _visit(value: object, lines: list[str], prefix: str, label: str) -> None:
    heading = f"{label}: " if label else ""
    if isinstance(value, (str, int, bool)) or value is None:
        lines.append(f"{prefix}{heading}{value!r}")
        return
    if isinstance(value, Enum):
        lines.append(f"{prefix}{heading}{value.name}")
        return
    if isinstance(value, (SourceSpan, SourcePosition)):
        return
    if isinstance(value, tuple):
        lines.append(f"{prefix}{heading}[{len(value)}]")
        for index, item in enumerate(value):
            _visit(item, lines, prefix + "  ", f"[{index}]")
        return
    if is_dataclass(value):
        lines.append(f"{prefix}{heading}{type(value).__name__}")
        for field in fields(value):
            if field.name == "span":
                continue
            _visit(getattr(value, field.name), lines, prefix + "  ", field.name)
        return
    lines.append(f"{prefix}{heading}{value!r}")
`````

## `code/minilang/minilang/cli.py`

`````python
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
`````

## `code/minilang/minilang/diagnostics.py`

`````python
"""Structured diagnostics shared by all MiniLang compiler stages."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .token import SourceSpan


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    severity: Severity
    code: str
    message: str
    span: SourceSpan


class DiagnosticBag:
    def __init__(self) -> None:
        self._items: list[Diagnostic] = []

    def report(self, severity: Severity, code: str, message: str, span: SourceSpan) -> None:
        self._items.append(Diagnostic(severity, code, message, span))

    def error(self, code: str, message: str, span: SourceSpan) -> None:
        self.report(Severity.ERROR, code, message, span)

    def warning(self, code: str, message: str, span: SourceSpan) -> None:
        self.report(Severity.WARNING, code, message, span)

    def note(self, code: str, message: str, span: SourceSpan) -> None:
        self.report(Severity.NOTE, code, message, span)

    def extend(self, diagnostics: Iterable[Diagnostic]) -> None:
        self._items.extend(diagnostics)

    @property
    def items(self) -> tuple[Diagnostic, ...]:
        return tuple(self._items)

    @property
    def has_errors(self) -> bool:
        return any(item.severity is Severity.ERROR for item in self._items)

    def __bool__(self) -> bool:
        return bool(self._items)


class CompilationError(RuntimeError):
    """Raised by the command-line driver after diagnostics have been printed."""


def render_diagnostic(source_name: str, source: str, diagnostic: Diagnostic) -> str:
    """Render a compact compiler-style diagnostic with a source underline."""
    lines = source.splitlines() or [""]
    line_index = max(0, diagnostic.span.start.line - 1)
    text = lines[line_index] if line_index < len(lines) else ""
    start_column = max(1, diagnostic.span.start.column)
    if diagnostic.span.end.line == diagnostic.span.start.line:
        width = max(1, diagnostic.span.end.column - start_column)
    else:
        width = max(1, len(text) - start_column + 2)
    underline = " " * (start_column - 1) + "^" + "~" * (width - 1)
    header = (
        f"{source_name}:{diagnostic.span.start.line}:{diagnostic.span.start.column}: "
        f"{diagnostic.severity.value}[{diagnostic.code}]: {diagnostic.message}"
    )
    return f"{header}\n{text}\n{underline}"
`````

## `code/minilang/minilang/driver.py`

`````python
"""Public compilation pipeline used by the CLI, tests, and book examples."""
from __future__ import annotations

from dataclasses import dataclass

from . import ast
from .diagnostics import Diagnostic
from .lexer import Lexer
from .optimizer import AstOptimizer, OptimizationStats
from .parser import Parser
from .semantic import AnalysisResult, SemanticAnalyzer


@dataclass(frozen=True, slots=True)
class CompilationUnit:
    source: str
    tokens: tuple
    program: ast.Program
    analysis: AnalysisResult
    diagnostics: tuple[Diagnostic, ...]
    optimization_stats: OptimizationStats | None = None

    @property
    def succeeded(self) -> bool:
        return not self.diagnostics


def compile_source(source: str, *, optimize: bool = False) -> CompilationUnit:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse_program()
    diagnostics: list[Diagnostic] = [*lexer.diagnostics.items, *parser.diagnostics.items]

    analysis = SemanticAnalyzer(program).analyze()
    diagnostics.extend(analysis.diagnostics)
    optimization_stats: OptimizationStats | None = None

    if optimize and not diagnostics:
        optimizer = AstOptimizer()
        program = optimizer.optimize(program)
        analysis = SemanticAnalyzer(program).analyze()
        diagnostics.extend(analysis.diagnostics)
        optimization_stats = optimizer.stats

    return CompilationUnit(
        source,
        tokens,
        program,
        analysis,
        tuple(diagnostics),
        optimization_stats,
    )
`````

## `code/minilang/minilang/interpreter.py`

`````python
"""Reference tree-walking evaluator for semantically valid MiniLang programs.

The interpreter is deliberately kept beside the LLVM backend. It acts as an
executable language specification and as a differential-testing oracle.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import TextIO

from . import ast
from .semantic import AnalysisResult
from .symbols import BuiltinSymbol, FunctionSymbol, Symbol, VariableSymbol


class MiniLangRuntimeError(RuntimeError):
    pass


@dataclass(slots=True)
class StructValue:
    type_name: str
    fields: dict[str, object]


class Environment:
    def __init__(self, parent: "Environment | None" = None) -> None:
        self.parent = parent
        self.values: dict[Symbol, object] = {}

    def define(self, symbol: Symbol, value: object) -> None:
        self.values[symbol] = value

    def get(self, symbol: Symbol) -> object:
        environment: Environment | None = self
        while environment is not None:
            if symbol in environment.values:
                return environment.values[symbol]
            environment = environment.parent
        raise MiniLangRuntimeError(f"uninitialized symbol {symbol.name!r}")

    def assign(self, symbol: Symbol, value: object) -> None:
        environment: Environment | None = self
        while environment is not None:
            if symbol in environment.values:
                environment.values[symbol] = value
                return
            environment = environment.parent
        raise MiniLangRuntimeError(f"assignment to uninitialized symbol {symbol.name!r}")


class _ReturnSignal(Exception):
    def __init__(self, value: object) -> None:
        self.value = value


class Interpreter:
    def __init__(self, program: ast.Program, analysis: AnalysisResult, output: TextIO | None = None) -> None:
        self.program = program
        self.analysis = analysis
        self.output = output if output is not None else StringIO()
        self.globals = Environment()
        self.environment = self.globals
        self.call_depth = 0
        self.max_call_depth = 1000

    def run(self) -> int:
        main = self.analysis.functions.get("main")
        if main is None:
            raise MiniLangRuntimeError("main function not found")
        result = self._call_function(main, [])
        if type(result) is not int:
            raise MiniLangRuntimeError("main did not return an integer")
        return result

    def _call_function(self, function: FunctionSymbol, arguments: list[object]) -> object:
        declaration = function.declaration
        if declaration is None:
            raise MiniLangRuntimeError(f"cannot directly call builtin {function.name}")
        if self.call_depth >= self.max_call_depth:
            raise MiniLangRuntimeError("maximum MiniLang call depth exceeded")
        self.call_depth += 1
        previous = self.environment
        frame = Environment(self.globals)
        self.environment = frame
        try:
            for parameter, value in zip(declaration.parameters, arguments):
                symbol = self.analysis.declarations.get(id(parameter))
                if not isinstance(symbol, VariableSymbol):
                    raise MiniLangRuntimeError(f"missing symbol for parameter {parameter.name}")
                frame.define(symbol, value)
            try:
                self._execute_block(declaration.body, create_environment=False)
            except _ReturnSignal as signal:
                return signal.value
            return None
        finally:
            self.environment = previous
            self.call_depth -= 1

    def _execute_block(self, block: ast.BlockStmt, create_environment: bool = True) -> None:
        previous = self.environment
        if create_environment:
            self.environment = Environment(previous)
        try:
            for statement in block.statements:
                self._execute(statement)
        finally:
            if create_environment:
                self.environment = previous

    def _execute(self, statement: ast.Stmt) -> None:
        if isinstance(statement, ast.BlockStmt):
            self._execute_block(statement)
            return
        if isinstance(statement, ast.LetStmt):
            value = self._evaluate(statement.initializer)
            symbol = self.analysis.declarations.get(id(statement))
            if not isinstance(symbol, VariableSymbol):
                raise MiniLangRuntimeError(f"missing symbol for variable {statement.name}")
            self.environment.define(symbol, value)
            return
        if isinstance(statement, ast.ExprStmt):
            self._evaluate(statement.expression)
            return
        if isinstance(statement, ast.IfStmt):
            if self._as_bool(self._evaluate(statement.condition)):
                self._execute_block(statement.then_branch)
            elif statement.else_branch is not None:
                if isinstance(statement.else_branch, ast.BlockStmt):
                    self._execute_block(statement.else_branch)
                else:
                    self._execute(statement.else_branch)
            return
        if isinstance(statement, ast.WhileStmt):
            while self._as_bool(self._evaluate(statement.condition)):
                self._execute_block(statement.body)
            return
        if isinstance(statement, ast.ForStmt):
            previous = self.environment
            self.environment = Environment(previous)
            try:
                if statement.initializer is not None:
                    self._execute(statement.initializer)
                while statement.condition is None or self._as_bool(self._evaluate(statement.condition)):
                    self._execute_block(statement.body)
                    if statement.increment is not None:
                        self._evaluate(statement.increment)
            finally:
                self.environment = previous
            return
        if isinstance(statement, ast.ReturnStmt):
            value = None if statement.value is None else self._evaluate(statement.value)
            raise _ReturnSignal(value)
        raise MiniLangRuntimeError(f"unhandled statement {type(statement).__name__}")

    def _evaluate(self, expression: ast.Expr) -> object:
        if isinstance(expression, ast.IntegerExpr):
            return expression.value
        if isinstance(expression, ast.BooleanExpr):
            return expression.value
        if isinstance(expression, ast.StringExpr):
            return expression.value
        if isinstance(expression, ast.ArrayExpr):
            return [self._evaluate(element) for element in expression.elements]
        if isinstance(expression, ast.StructInitExpr):
            return StructValue(
                expression.name,
                {field.name: self._evaluate(field.value) for field in expression.fields},
            )
        if isinstance(expression, ast.NameExpr):
            symbol = self.analysis.bindings.get(id(expression))
            if isinstance(symbol, VariableSymbol):
                return self.environment.get(symbol)
            if isinstance(symbol, (FunctionSymbol, BuiltinSymbol)):
                return symbol
            raise MiniLangRuntimeError(f"unresolved name {expression.name!r}")
        if isinstance(expression, ast.UnaryExpr):
            operand = self._evaluate(expression.operand)
            if expression.operator == "-":
                return -self._as_int(operand)
            if expression.operator == "+":
                return self._as_int(operand)
            if expression.operator == "!":
                return not self._as_bool(operand)
            raise MiniLangRuntimeError(f"unknown unary operator {expression.operator}")
        if isinstance(expression, ast.BinaryExpr):
            if expression.operator == "&&":
                left = self._as_bool(self._evaluate(expression.left))
                return left and self._as_bool(self._evaluate(expression.right))
            if expression.operator == "||":
                left = self._as_bool(self._evaluate(expression.left))
                return left or self._as_bool(self._evaluate(expression.right))
            left = self._evaluate(expression.left)
            right = self._evaluate(expression.right)
            op = expression.operator
            if op == "+":
                return self._as_int(left) + self._as_int(right)
            if op == "-":
                return self._as_int(left) - self._as_int(right)
            if op == "*":
                return self._as_int(left) * self._as_int(right)
            if op == "/":
                return self._truncating_division(self._as_int(left), self._as_int(right))
            if op == "%":
                a, b = self._as_int(left), self._as_int(right)
                return a - self._truncating_division(a, b) * b
            if op == "<":
                return self._as_int(left) < self._as_int(right)
            if op == "<=":
                return self._as_int(left) <= self._as_int(right)
            if op == ">":
                return self._as_int(left) > self._as_int(right)
            if op == ">=":
                return self._as_int(left) >= self._as_int(right)
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            raise MiniLangRuntimeError(f"unknown binary operator {op}")
        if isinstance(expression, ast.AssignExpr):
            value = self._evaluate(expression.value)
            self._assign(expression.target, value)
            return value
        if isinstance(expression, ast.IndexExpr):
            collection = self._evaluate(expression.collection)
            index = self._as_int(self._evaluate(expression.index))
            if not isinstance(collection, list):
                raise MiniLangRuntimeError("indexing non-array value")
            if index < 0 or index >= len(collection):
                raise MiniLangRuntimeError(f"array index {index} out of bounds for length {len(collection)}")
            return collection[index]
        if isinstance(expression, ast.FieldExpr):
            receiver = self._evaluate(expression.receiver)
            if not isinstance(receiver, StructValue):
                raise MiniLangRuntimeError("field access on non-structure value")
            try:
                return receiver.fields[expression.name]
            except KeyError as exc:
                raise MiniLangRuntimeError(f"missing field {expression.name!r}") from exc
        if isinstance(expression, ast.CallExpr):
            if isinstance(expression.callee, ast.NameExpr) and expression.callee.name == "len":
                if len(expression.arguments) != 1:
                    raise MiniLangRuntimeError("len expects one argument")
                value = self._evaluate(expression.arguments[0])
                if not isinstance(value, (list, str)):
                    raise MiniLangRuntimeError("len expects array or string")
                return len(value)
            callee = self._evaluate(expression.callee)
            arguments = [self._evaluate(argument) for argument in expression.arguments]
            if isinstance(callee, BuiltinSymbol):
                return self._call_builtin(callee.name, arguments)
            if isinstance(callee, FunctionSymbol):
                return self._call_function(callee, arguments)
            raise MiniLangRuntimeError("attempted to call non-function value")
        raise MiniLangRuntimeError(f"unhandled expression {type(expression).__name__}")

    def _assign(self, target: ast.Expr, value: object) -> None:
        if isinstance(target, ast.NameExpr):
            symbol = self.analysis.bindings.get(id(target))
            if not isinstance(symbol, VariableSymbol):
                raise MiniLangRuntimeError("assignment target is not a variable")
            self.environment.assign(symbol, value)
            return
        if isinstance(target, ast.IndexExpr):
            collection = self._evaluate(target.collection)
            index = self._as_int(self._evaluate(target.index))
            if not isinstance(collection, list):
                raise MiniLangRuntimeError("index assignment requires an array")
            if index < 0 or index >= len(collection):
                raise MiniLangRuntimeError(f"array index {index} out of bounds for length {len(collection)}")
            collection[index] = value
            return
        if isinstance(target, ast.FieldExpr):
            receiver = self._evaluate(target.receiver)
            if not isinstance(receiver, StructValue):
                raise MiniLangRuntimeError("field assignment requires a structure")
            receiver.fields[target.name] = value
            return
        raise MiniLangRuntimeError("invalid assignment target")

    def _call_builtin(self, name: str, arguments: list[object]) -> object:
        if name == "print_int":
            print(self._as_int(arguments[0]), file=self.output)
            return None
        if name == "print_bool":
            print("true" if self._as_bool(arguments[0]) else "false", file=self.output)
            return None
        if name == "print_string":
            value = arguments[0]
            if not isinstance(value, str):
                raise MiniLangRuntimeError("print_string expects a string")
            print(value, file=self.output)
            return None
        if name == "assert":
            if not self._as_bool(arguments[0]):
                raise MiniLangRuntimeError("assertion failed")
            return None
        raise MiniLangRuntimeError(f"unknown builtin {name}")

    @staticmethod
    def _truncating_division(left: int, right: int) -> int:
        if right == 0:
            raise MiniLangRuntimeError("division by zero")
        quotient = abs(left) // abs(right)
        return -quotient if (left < 0) ^ (right < 0) else quotient

    @staticmethod
    def _as_int(value: object) -> int:
        if type(value) is not int:
            raise MiniLangRuntimeError(f"expected int, got {type(value).__name__}")
        return value

    @staticmethod
    def _as_bool(value: object) -> bool:
        if type(value) is not bool:
            raise MiniLangRuntimeError(f"expected bool, got {type(value).__name__}")
        return value
`````

## `code/minilang/minilang/lexer.py`

`````python
"""A hand-written deterministic scanner for MiniLang."""
from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import DiagnosticBag
from .token import KEYWORDS, SourcePosition, SourceSpan, Token, TokenKind


@dataclass(slots=True)
class _Cursor:
    offset: int = 0
    line: int = 1
    column: int = 1

    def position(self) -> SourcePosition:
        return SourcePosition(self.offset, self.line, self.column)


class Lexer:
    """Convert source text into tokens in one left-to-right pass.

    The implementation recognizes nested block comments, escaped strings,
    binary/hexadecimal integers, and Unicode identifiers. Invalid input is
    represented by ERROR tokens and diagnostics so the parser can continue.
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.cursor = _Cursor()
        self.diagnostics = DiagnosticBag()

    def tokenize(self) -> tuple[Token, ...]:
        tokens: list[Token] = []
        while not self._at_end():
            self._skip_trivia()
            if self._at_end():
                break
            tokens.append(self._scan_token())
        position = self.cursor.position()
        tokens.append(Token(TokenKind.EOF, "", None, SourceSpan(position, position)))
        return tuple(tokens)

    def _scan_token(self) -> Token:
        start = self.cursor.position()
        ch = self._advance()

        if ch.isalpha() or ch == "_":
            return self._identifier(start)
        if ch.isdigit():
            return self._number(start, ch)
        if ch == '"':
            return self._string(start)

        single = {
            "(": TokenKind.LEFT_PAREN,
            ")": TokenKind.RIGHT_PAREN,
            "{": TokenKind.LEFT_BRACE,
            "}": TokenKind.RIGHT_BRACE,
            "[": TokenKind.LEFT_BRACKET,
            "]": TokenKind.RIGHT_BRACKET,
            ",": TokenKind.COMMA,
            ".": TokenKind.DOT,
            ":": TokenKind.COLON,
            ";": TokenKind.SEMICOLON,
            "+": TokenKind.PLUS,
            "*": TokenKind.STAR,
            "/": TokenKind.SLASH,
            "%": TokenKind.PERCENT,
        }
        if ch in single:
            return self._token(single[ch], start)

        if ch == "-":
            if self._match(">"):
                return self._token(TokenKind.ARROW, start)
            return self._token(TokenKind.MINUS, start)
        if ch == "!":
            return self._token(TokenKind.BANG_EQUAL if self._match("=") else TokenKind.BANG, start)
        if ch == "=":
            return self._token(TokenKind.EQUAL_EQUAL if self._match("=") else TokenKind.EQUAL, start)
        if ch == "<":
            return self._token(TokenKind.LESS_EQUAL if self._match("=") else TokenKind.LESS, start)
        if ch == ">":
            return self._token(TokenKind.GREATER_EQUAL if self._match("=") else TokenKind.GREATER, start)
        if ch == "&" and self._match("&"):
            return self._token(TokenKind.AND_AND, start)
        if ch == "|" and self._match("|"):
            return self._token(TokenKind.OR_OR, start)

        span = SourceSpan(start, self.cursor.position())
        self.diagnostics.error("LEX001", f"unexpected character {ch!r}", span)
        return Token(TokenKind.ERROR, self._slice(start), ch, span)

    def _skip_trivia(self) -> None:
        while not self._at_end():
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
                continue
            if ch == "/" and self._peek(1) == "/":
                self._advance()
                self._advance()
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
                continue
            if ch == "/" and self._peek(1) == "*":
                self._skip_block_comment()
                continue
            break

    def _skip_block_comment(self) -> None:
        start = self.cursor.position()
        self._advance()
        self._advance()
        depth = 1
        while depth and not self._at_end():
            if self._peek() == "/" and self._peek(1) == "*":
                self._advance()
                self._advance()
                depth += 1
            elif self._peek() == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                depth -= 1
            else:
                self._advance()
        if depth:
            self.diagnostics.error(
                "LEX002",
                "unterminated block comment",
                SourceSpan(start, self.cursor.position()),
            )

    def _identifier(self, start: SourcePosition) -> Token:
        while True:
            ch = self._peek()
            if not (ch.isalnum() or ch == "_"):
                break
            self._advance()
        lexeme = self._slice(start)
        return self._token(KEYWORDS.get(lexeme, TokenKind.IDENTIFIER), start)

    def _number(self, start: SourcePosition, first: str) -> Token:
        base = 10
        if first == "0" and self._peek() in {"x", "X", "b", "B"}:
            marker = self._advance().lower()
            base = 16 if marker == "x" else 2
            valid = "0123456789abcdefABCDEF" if base == 16 else "01"
            digit_count = 0
            while self._peek() in valid or self._peek() == "_":
                if self._peek() != "_":
                    digit_count += 1
                self._advance()
            if digit_count == 0:
                span = SourceSpan(start, self.cursor.position())
                self.diagnostics.error("LEX003", f"base-{base} literal requires at least one digit", span)
                return Token(TokenKind.ERROR, self._slice(start), None, span)
        else:
            while self._peek().isdigit() or self._peek() == "_":
                self._advance()

        lexeme = self._slice(start)
        try:
            value = int(lexeme.replace("_", ""), base)
        except ValueError:
            span = SourceSpan(start, self.cursor.position())
            self.diagnostics.error("LEX004", f"invalid integer literal {lexeme!r}", span)
            return Token(TokenKind.ERROR, lexeme, None, span)
        return self._token(TokenKind.INTEGER, start, value)

    def _string(self, start: SourcePosition) -> Token:
        value: list[str] = []
        escapes = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\", "0": "\0"}
        terminated = False
        while not self._at_end():
            ch = self._advance()
            if ch == '"':
                terminated = True
                break
            if ch == "\n":
                break
            if ch == "\\":
                if self._at_end():
                    break
                escaped = self._advance()
                if escaped == "u" and self._peek() == "{":
                    value.append(self._unicode_escape(start))
                elif escaped in escapes:
                    value.append(escapes[escaped])
                else:
                    span = SourceSpan(start, self.cursor.position())
                    self.diagnostics.error("LEX005", f"unknown escape sequence \\{escaped}", span)
                    value.append(escaped)
            else:
                value.append(ch)

        span = SourceSpan(start, self.cursor.position())
        if not terminated:
            self.diagnostics.error("LEX006", "unterminated string literal", span)
            return Token(TokenKind.ERROR, self._slice(start), "".join(value), span)
        return Token(TokenKind.STRING, self._slice(start), "".join(value), span)

    def _unicode_escape(self, string_start: SourcePosition) -> str:
        self._advance()  # '{'
        digits: list[str] = []
        while not self._at_end() and self._peek() != "}" and len(digits) < 6:
            digits.append(self._advance())
        if not self._match("}"):
            self.diagnostics.error(
                "LEX007",
                "unterminated Unicode escape; expected '}'",
                SourceSpan(string_start, self.cursor.position()),
            )
            return "�"
        try:
            value = int("".join(digits), 16)
            return chr(value)
        except (ValueError, OverflowError):
            self.diagnostics.error(
                "LEX008",
                f"invalid Unicode scalar value {''.join(digits)!r}",
                SourceSpan(string_start, self.cursor.position()),
            )
            return "�"

    def _token(self, kind: TokenKind, start: SourcePosition, literal: object | None = None) -> Token:
        return Token(kind, self._slice(start), literal, SourceSpan(start, self.cursor.position()))

    def _slice(self, start: SourcePosition) -> str:
        return self.source[start.offset : self.cursor.offset]

    def _at_end(self) -> bool:
        return self.cursor.offset >= len(self.source)

    def _peek(self, distance: int = 0) -> str:
        index = self.cursor.offset + distance
        return "\0" if index >= len(self.source) else self.source[index]

    def _match(self, expected: str) -> bool:
        if self._peek() != expected:
            return False
        self._advance()
        return True

    def _advance(self) -> str:
        ch = self.source[self.cursor.offset]
        self.cursor.offset += 1
        if ch == "\n":
            self.cursor.line += 1
            self.cursor.column = 1
        elif ch == "\t":
            self.cursor.column += 4
        else:
            self.cursor.column += 1
        return ch
`````

## `code/minilang/minilang/llvm_backend.py`

`````python
"""LLVM IR backend for the MiniLang teaching compiler.

The backend emits modern opaque-pointer LLVM IR and intentionally keeps local
variables in stack slots. Running `opt -passes=mem2reg` or compiling with
`clang -O1` demonstrates promotion to SSA form.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ast
from .semantic import AnalysisResult
from .symbols import BuiltinSymbol, FunctionSymbol, VariableSymbol
from .typesys import ArrayType, BOOL, ERROR, INT, STRING, VOID, FunctionType, StructType, Type


class CodegenError(RuntimeError):
    pass


@dataclass(slots=True)
class _Block:
    label: str
    instructions: list[str] = field(default_factory=list)
    terminated: bool = False


@dataclass(frozen=True, slots=True)
class _Value:
    type: Type
    operand: str


class LLVMBackend:
    def __init__(self, program: ast.Program, analysis: AnalysisResult, module_name: str = "minilang") -> None:
        self.program = program
        self.analysis = analysis
        self.module_name = module_name
        self.functions_text: list[str] = []
        self.string_globals: dict[str, tuple[str, int]] = {}
        self.string_order: list[str] = []
        self.register_counter = 0
        self.label_counter = 0
        self.temp_counter = 0
        self.blocks: list[_Block] = []
        self.current: _Block | None = None
        self.entry_allocas: list[str] = []
        self.storage: dict[VariableSymbol, str] = {}
        self.current_function: FunctionSymbol | None = None

    def emit(self) -> str:
        for declaration in self.program.declarations:
            if isinstance(declaration, ast.FunctionDecl):
                symbol = self.analysis.functions.get(declaration.name)
                if symbol is None or symbol.declaration is not declaration:
                    # Optimized trees are reanalyzed; this guard mainly protects
                    # malformed clients that mix a tree with another analysis.
                    symbol = self.analysis.declarations.get(id(declaration))  # type: ignore[assignment]
                if not isinstance(symbol, FunctionSymbol):
                    raise CodegenError(f"missing function symbol for {declaration.name}")
                self.functions_text.append(self._emit_function(declaration, symbol))

        lines = [
            f"; ModuleID = '{self.module_name}'",
            f'source_filename = "{self._escape_identifier(self.module_name)}"',
            "",
            "%MiniLangBoolText = type { ptr }",
        ]
        for name in sorted(self.analysis.structs):
            struct_type = self.analysis.structs[name].type
            fields = ", ".join(self._llvm_type(type_) for _, type_ in struct_type.fields)
            lines.append(f"%struct.{self._mangle(name)} = type {{ {fields} }}")
        lines.extend(
            [
                "",
                '@.fmt.int = private unnamed_addr constant [5 x i8] c"%ld\\0A\\00", align 1',
                '@.bool.true = private unnamed_addr constant [5 x i8] c"true\\00", align 1',
                '@.bool.false = private unnamed_addr constant [6 x i8] c"false\\00", align 1',
                '@.assert.msg = private unnamed_addr constant [26 x i8] c"MiniLang assertion failed\\00", align 1',
            ]
        )
        for value in self.string_order:
            global_name, length = self.string_globals[value]
            encoded = self._llvm_c_string(value)
            lines.append(
                f"{global_name} = private unnamed_addr constant [{length} x i8] c\"{encoded}\", align 1"
            )
        lines.extend(
            [
                "",
                "declare i32 @printf(ptr, ...)",
                "declare i32 @puts(ptr)",
                "declare i64 @strlen(ptr)",
                "declare i32 @strcmp(ptr, ptr)",
                "declare void @abort() noreturn nounwind",
                "",
            ]
        )
        lines.extend(self.functions_text)
        return "\n".join(lines).rstrip() + "\n"

    def _emit_function(self, declaration: ast.FunctionDecl, symbol: FunctionSymbol) -> str:
        if isinstance(symbol.type.return_type, (ArrayType, StructType)):
            raise CodegenError("aggregate return values are not supported by this compact backend")

        self.register_counter = 0
        self.label_counter = 0
        self.temp_counter = 0
        self.blocks = []
        self.entry_allocas = []
        self.storage = {}
        self.current_function = symbol
        entry = self._new_block("entry")

        parameters: list[str] = []
        for index, (parameter, type_) in enumerate(zip(declaration.parameters, symbol.type.parameters)):
            argument_name = f"%arg.{self._mangle(parameter.name)}.{index}"
            parameters.append(f"{self._parameter_type(type_)} {argument_name}")
            parameter_symbol = self.analysis.declarations.get(id(parameter))
            if not isinstance(parameter_symbol, VariableSymbol):
                raise CodegenError(f"missing parameter symbol for {parameter.name}")
            if self._is_aggregate(type_):
                slot = self._alloca(type_, parameter.name)
                self._copy_aggregate(slot, argument_name, type_)
                self.storage[parameter_symbol] = slot
            else:
                slot = self._alloca(type_, parameter.name)
                self._emit(f"store {self._llvm_type(type_)} {argument_name}, ptr {slot}, align {self._alignment(type_)}")
                self.storage[parameter_symbol] = slot

        self._emit_block_statement(declaration.body, create_scope=False)
        if not self._block().terminated:
            if symbol.type.return_type == VOID:
                self._terminate("ret void")
            else:
                self._terminate("unreachable")

        # All allocas are inserted at the start of entry so mem2reg can see them.
        entry.instructions[0:0] = self.entry_allocas
        header = (
            f"define {self._llvm_type(symbol.type.return_type)} @{self._mangle(declaration.name)}"
            f"({', '.join(parameters)}) {{"
        )
        output = [header]
        for block in self.blocks:
            output.append(f"{block.label}:")
            output.extend(f"  {instruction}" for instruction in block.instructions)
            if not block.terminated:
                output.append("  unreachable")
        output.append("}")
        output.append("")
        return "\n".join(output)

    def _emit_block_statement(self, block: ast.BlockStmt, create_scope: bool = True) -> None:
        # Storage is keyed by unique semantic symbols, so no explicit backend
        # scope stack is required. create_scope is retained to mirror the front end.
        _ = create_scope
        for statement in block.statements:
            if self._block().terminated:
                break
            self._emit_statement(statement)

    def _emit_statement(self, statement: ast.Stmt) -> None:
        if isinstance(statement, ast.BlockStmt):
            self._emit_block_statement(statement)
            return
        if isinstance(statement, ast.LetStmt):
            symbol = self.analysis.declarations.get(id(statement))
            if not isinstance(symbol, VariableSymbol):
                raise CodegenError(f"missing variable symbol for {statement.name}")
            value = self._emit_expression(statement.initializer)
            if self._is_aggregate(symbol.type):
                slot = self._alloca(symbol.type, statement.name)
                self._copy_aggregate(slot, value.operand, symbol.type)
            else:
                slot = self._alloca(symbol.type, statement.name)
                self._emit(
                    f"store {self._llvm_type(symbol.type)} {value.operand}, ptr {slot}, align {self._alignment(symbol.type)}"
                )
            self.storage[symbol] = slot
            return
        if isinstance(statement, ast.ExprStmt):
            self._emit_expression(statement.expression)
            return
        if isinstance(statement, ast.ReturnStmt):
            assert self.current_function is not None
            if statement.value is None:
                self._terminate("ret void")
            else:
                value = self._emit_expression(statement.value)
                self._terminate(f"ret {self._llvm_type(value.type)} {value.operand}")
            return
        if isinstance(statement, ast.IfStmt):
            self._emit_if(statement)
            return
        if isinstance(statement, ast.WhileStmt):
            self._emit_while(statement)
            return
        if isinstance(statement, ast.ForStmt):
            self._emit_for(statement)
            return
        raise CodegenError(f"unhandled statement {type(statement).__name__}")

    def _emit_if(self, statement: ast.IfStmt) -> None:
        condition = self._emit_expression(statement.condition)
        then_label = self._fresh_label("if.then")
        else_label = self._fresh_label("if.else")
        end_label = self._fresh_label("if.end")
        self._terminate(f"br i1 {condition.operand}, label %{then_label}, label %{else_label}")

        self._new_block(then_label)
        self._emit_block_statement(statement.then_branch)
        then_falls_through = not self._block().terminated
        if then_falls_through:
            self._terminate(f"br label %{end_label}")

        self._new_block(else_label)
        if isinstance(statement.else_branch, ast.BlockStmt):
            self._emit_block_statement(statement.else_branch)
        elif isinstance(statement.else_branch, ast.IfStmt):
            self._emit_statement(statement.else_branch)
        else:
            pass
        else_falls_through = not self._block().terminated
        if else_falls_through:
            self._terminate(f"br label %{end_label}")

        self._new_block(end_label)
        if not then_falls_through and not else_falls_through:
            self._terminate("unreachable")

    def _emit_while(self, statement: ast.WhileStmt) -> None:
        condition_label = self._fresh_label("while.cond")
        body_label = self._fresh_label("while.body")
        end_label = self._fresh_label("while.end")
        self._terminate(f"br label %{condition_label}")

        self._new_block(condition_label)
        condition = self._emit_expression(statement.condition)
        self._terminate(f"br i1 {condition.operand}, label %{body_label}, label %{end_label}")

        self._new_block(body_label)
        self._emit_block_statement(statement.body)
        if not self._block().terminated:
            self._terminate(f"br label %{condition_label}")

        self._new_block(end_label)

    def _emit_for(self, statement: ast.ForStmt) -> None:
        if statement.initializer is not None:
            self._emit_statement(statement.initializer)
        condition_label = self._fresh_label("for.cond")
        body_label = self._fresh_label("for.body")
        increment_label = self._fresh_label("for.inc")
        end_label = self._fresh_label("for.end")
        self._terminate(f"br label %{condition_label}")

        self._new_block(condition_label)
        if statement.condition is None:
            condition = _Value(BOOL, "true")
        else:
            condition = self._emit_expression(statement.condition)
        self._terminate(f"br i1 {condition.operand}, label %{body_label}, label %{end_label}")

        self._new_block(body_label)
        self._emit_block_statement(statement.body)
        if not self._block().terminated:
            self._terminate(f"br label %{increment_label}")

        self._new_block(increment_label)
        if statement.increment is not None:
            self._emit_expression(statement.increment)
        if not self._block().terminated:
            self._terminate(f"br label %{condition_label}")

        self._new_block(end_label)

    def _emit_expression(self, expression: ast.Expr) -> _Value:
        type_ = self.analysis.type_of(expression)
        if type_.is_error:
            raise CodegenError(f"cannot generate code for erroneous expression {type(expression).__name__}")
        if isinstance(expression, ast.IntegerExpr):
            return _Value(INT, str(expression.value))
        if isinstance(expression, ast.BooleanExpr):
            return _Value(BOOL, "true" if expression.value else "false")
        if isinstance(expression, ast.StringExpr):
            name, length = self._intern_string(expression.value)
            register = self._register()
            self._emit(
                f"{register} = getelementptr inbounds [{length} x i8], ptr {name}, i64 0, i64 0"
            )
            return _Value(STRING, register)
        if isinstance(expression, ast.ArrayExpr):
            assert isinstance(type_, ArrayType)
            pointer = self._alloca(type_, "array.literal")
            for index, element in enumerate(expression.elements):
                element_value = self._emit_expression(element)
                element_pointer = self._register()
                llvm_array = self._llvm_type(type_)
                self._emit(
                    f"{element_pointer} = getelementptr inbounds {llvm_array}, ptr {pointer}, i64 0, i64 {index}"
                )
                if self._is_aggregate(type_.element):
                    self._copy_aggregate(element_pointer, element_value.operand, type_.element)
                else:
                    self._emit(
                        f"store {self._llvm_type(type_.element)} {element_value.operand}, ptr {element_pointer}, "
                        f"align {self._alignment(type_.element)}"
                    )
            return _Value(type_, pointer)
        if isinstance(expression, ast.StructInitExpr):
            assert isinstance(type_, StructType)
            pointer = self._alloca(type_, f"{type_.name}.literal")
            by_name = {field.name: field.value for field in expression.fields}
            for index, (field_name, field_type) in enumerate(type_.fields):
                value = self._emit_expression(by_name[field_name])
                field_pointer = self._register()
                self._emit(
                    f"{field_pointer} = getelementptr inbounds {self._llvm_type(type_)}, ptr {pointer}, i32 0, i32 {index}"
                )
                if self._is_aggregate(field_type):
                    self._copy_aggregate(field_pointer, value.operand, field_type)
                else:
                    self._emit(
                        f"store {self._llvm_type(field_type)} {value.operand}, ptr {field_pointer}, "
                        f"align {self._alignment(field_type)}"
                    )
            return _Value(type_, pointer)
        if isinstance(expression, ast.NameExpr):
            symbol = self.analysis.bindings.get(id(expression))
            if isinstance(symbol, VariableSymbol):
                pointer = self.storage.get(symbol)
                if pointer is None:
                    raise CodegenError(f"no storage for variable {symbol.name}")
                if self._is_aggregate(symbol.type):
                    return _Value(symbol.type, pointer)
                register = self._register()
                self._emit(
                    f"{register} = load {self._llvm_type(symbol.type)}, ptr {pointer}, align {self._alignment(symbol.type)}"
                )
                return _Value(symbol.type, register)
            if isinstance(symbol, (FunctionSymbol, BuiltinSymbol)):
                return _Value(symbol.type or ERROR, f"@{self._mangle(symbol.name)}")
            raise CodegenError(f"unresolved name {expression.name}")
        if isinstance(expression, ast.UnaryExpr):
            operand = self._emit_expression(expression.operand)
            register = self._register()
            if expression.operator == "-":
                self._emit(f"{register} = sub i64 0, {operand.operand}")
                return _Value(INT, register)
            if expression.operator == "+":
                return operand
            if expression.operator == "!":
                self._emit(f"{register} = xor i1 {operand.operand}, true")
                return _Value(BOOL, register)
            raise CodegenError(f"unknown unary operator {expression.operator}")
        if isinstance(expression, ast.BinaryExpr):
            if expression.operator in {"&&", "||"}:
                return self._emit_short_circuit(expression)
            left = self._emit_expression(expression.left)
            right = self._emit_expression(expression.right)
            return self._emit_binary(expression.operator, left, right)
        if isinstance(expression, ast.AssignExpr):
            pointer, target_type = self._emit_lvalue(expression.target)
            value = self._emit_expression(expression.value)
            if self._is_aggregate(target_type):
                self._copy_aggregate(pointer, value.operand, target_type)
                return _Value(target_type, pointer)
            self._emit(
                f"store {self._llvm_type(target_type)} {value.operand}, ptr {pointer}, align {self._alignment(target_type)}"
            )
            return _Value(target_type, value.operand)
        if isinstance(expression, ast.IndexExpr):
            pointer, element_type = self._emit_lvalue(expression)
            if self._is_aggregate(element_type):
                return _Value(element_type, pointer)
            register = self._register()
            self._emit(
                f"{register} = load {self._llvm_type(element_type)}, ptr {pointer}, align {self._alignment(element_type)}"
            )
            return _Value(element_type, register)
        if isinstance(expression, ast.FieldExpr):
            pointer, field_type = self._emit_lvalue(expression)
            if self._is_aggregate(field_type):
                return _Value(field_type, pointer)
            register = self._register()
            self._emit(
                f"{register} = load {self._llvm_type(field_type)}, ptr {pointer}, align {self._alignment(field_type)}"
            )
            return _Value(field_type, register)
        if isinstance(expression, ast.CallExpr):
            return self._emit_call(expression)
        raise CodegenError(f"unhandled expression {type(expression).__name__}")

    def _emit_lvalue(self, expression: ast.Expr) -> tuple[str, Type]:
        if isinstance(expression, ast.NameExpr):
            symbol = self.analysis.bindings.get(id(expression))
            if not isinstance(symbol, VariableSymbol):
                raise CodegenError("name is not assignable")
            pointer = self.storage.get(symbol)
            if pointer is None:
                raise CodegenError(f"no storage for {symbol.name}")
            return pointer, symbol.type
        if isinstance(expression, ast.IndexExpr):
            collection = self._emit_expression(expression.collection)
            if not isinstance(collection.type, ArrayType):
                raise CodegenError("indexing non-array")
            index = self._emit_expression(expression.index)
            self._emit_bounds_check(index.operand, collection.type.length)
            pointer = self._register()
            self._emit(
                f"{pointer} = getelementptr inbounds {self._llvm_type(collection.type)}, ptr {collection.operand}, "
                f"i64 0, i64 {index.operand}"
            )
            return pointer, collection.type.element
        if isinstance(expression, ast.FieldExpr):
            receiver = self._emit_expression(expression.receiver)
            if not isinstance(receiver.type, StructType):
                raise CodegenError("field access on non-structure")
            index = receiver.type.field_index(expression.name)
            field_type = receiver.type.field_type(expression.name)
            if index is None or field_type is None:
                raise CodegenError(f"unknown field {expression.name}")
            pointer = self._register()
            self._emit(
                f"{pointer} = getelementptr inbounds {self._llvm_type(receiver.type)}, ptr {receiver.operand}, "
                f"i32 0, i32 {index}"
            )
            return pointer, field_type
        raise CodegenError("invalid lvalue")

    def _emit_call(self, expression: ast.CallExpr) -> _Value:
        if isinstance(expression.callee, ast.NameExpr):
            name = expression.callee.name
            if name == "len":
                argument = self._emit_expression(expression.arguments[0])
                if isinstance(argument.type, ArrayType):
                    return _Value(INT, str(argument.type.length))
                register = self._register()
                self._emit(f"{register} = call i64 @strlen(ptr {argument.operand})")
                return _Value(INT, register)
            if name == "print_int":
                value = self._emit_expression(expression.arguments[0])
                format_pointer = self._register()
                self._emit(
                    f"{format_pointer} = getelementptr inbounds [5 x i8], ptr @.fmt.int, i64 0, i64 0"
                )
                call_result = self._register()
                self._emit(f"{call_result} = call i32 (ptr, ...) @printf(ptr {format_pointer}, i64 {value.operand})")
                return _Value(VOID, "")
            if name == "print_string":
                value = self._emit_expression(expression.arguments[0])
                call_result = self._register()
                self._emit(f"{call_result} = call i32 @puts(ptr {value.operand})")
                return _Value(VOID, "")
            if name == "print_bool":
                value = self._emit_expression(expression.arguments[0])
                pointer = self._register()
                self._emit(f"{pointer} = select i1 {value.operand}, ptr @.bool.true, ptr @.bool.false")
                call_result = self._register()
                self._emit(f"{call_result} = call i32 @puts(ptr {pointer})")
                return _Value(VOID, "")
            if name == "assert":
                condition = self._emit_expression(expression.arguments[0])
                ok_label = self._fresh_label("assert.ok")
                fail_label = self._fresh_label("assert.fail")
                self._terminate(f"br i1 {condition.operand}, label %{ok_label}, label %{fail_label}")
                self._new_block(fail_label)
                message_pointer = self._register()
                self._emit(
                    f"{message_pointer} = getelementptr inbounds [26 x i8], ptr @.assert.msg, i64 0, i64 0"
                )
                ignored = self._register()
                self._emit(f"{ignored} = call i32 @puts(ptr {message_pointer})")
                self._emit("call void @abort()")
                self._terminate("unreachable")
                self._new_block(ok_label)
                return _Value(VOID, "")

        callee_symbol = None
        if isinstance(expression.callee, ast.NameExpr):
            callee_symbol = self.analysis.bindings.get(id(expression.callee))
        if not isinstance(callee_symbol, FunctionSymbol):
            raise CodegenError("LLVM backend supports direct function calls only")
        arguments: list[str] = []
        for argument_expression, parameter_type in zip(expression.arguments, callee_symbol.type.parameters):
            value = self._emit_expression(argument_expression)
            if self._is_aggregate(parameter_type):
                copy = self._alloca(parameter_type, "arg.copy")
                self._copy_aggregate(copy, value.operand, parameter_type)
                arguments.append(f"ptr {copy}")
            else:
                arguments.append(f"{self._llvm_type(parameter_type)} {value.operand}")
        return_type = callee_symbol.type.return_type
        if return_type == VOID:
            self._emit(f"call void @{self._mangle(callee_symbol.name)}({', '.join(arguments)})")
            return _Value(VOID, "")
        register = self._register()
        self._emit(
            f"{register} = call {self._llvm_type(return_type)} @{self._mangle(callee_symbol.name)}"
            f"({', '.join(arguments)})"
        )
        return _Value(return_type, register)

    def _emit_binary(self, operator: str, left: _Value, right: _Value) -> _Value:
        register = self._register()
        if operator == "+":
            self._emit(f"{register} = add i64 {left.operand}, {right.operand}")
            return _Value(INT, register)
        if operator == "-":
            self._emit(f"{register} = sub i64 {left.operand}, {right.operand}")
            return _Value(INT, register)
        if operator == "*":
            self._emit(f"{register} = mul i64 {left.operand}, {right.operand}")
            return _Value(INT, register)
        if operator in {"/", "%"}:
            self._emit_nonzero_check(right.operand)
            opcode = "sdiv" if operator == "/" else "srem"
            self._emit(f"{register} = {opcode} i64 {left.operand}, {right.operand}")
            return _Value(INT, register)
        comparisons = {"<": "slt", "<=": "sle", ">": "sgt", ">=": "sge"}
        if operator in comparisons:
            self._emit(f"{register} = icmp {comparisons[operator]} i64 {left.operand}, {right.operand}")
            return _Value(BOOL, register)
        if operator in {"==", "!="}:
            predicate = "eq" if operator == "==" else "ne"
            if left.type == STRING:
                comparison = self._register()
                self._emit(f"{comparison} = call i32 @strcmp(ptr {left.operand}, ptr {right.operand})")
                self._emit(f"{register} = icmp {predicate} i32 {comparison}, 0")
            else:
                self._emit(
                    f"{register} = icmp {predicate} {self._llvm_type(left.type)} {left.operand}, {right.operand}"
                )
            return _Value(BOOL, register)
        raise CodegenError(f"unknown binary operator {operator}")

    def _emit_short_circuit(self, expression: ast.BinaryExpr) -> _Value:
        left = self._emit_expression(expression.left)
        left_block = self._block().label
        rhs_label = self._fresh_label("logic.rhs")
        end_label = self._fresh_label("logic.end")
        if expression.operator == "&&":
            self._terminate(f"br i1 {left.operand}, label %{rhs_label}, label %{end_label}")
            short_value = "false"
        else:
            self._terminate(f"br i1 {left.operand}, label %{end_label}, label %{rhs_label}")
            short_value = "true"
        self._new_block(rhs_label)
        right = self._emit_expression(expression.right)
        right_block = self._block().label
        self._terminate(f"br label %{end_label}")
        self._new_block(end_label)
        result = self._register()
        self._emit(f"{result} = phi i1 [{short_value}, %{left_block}], [{right.operand}, %{right_block}]")
        return _Value(BOOL, result)

    def _emit_bounds_check(self, index: str, length: int) -> None:
        nonnegative = self._register()
        below_length = self._register()
        in_range = self._register()
        ok_label = self._fresh_label("index.ok")
        fail_label = self._fresh_label("index.fail")
        self._emit(f"{nonnegative} = icmp sge i64 {index}, 0")
        self._emit(f"{below_length} = icmp slt i64 {index}, {length}")
        self._emit(f"{in_range} = and i1 {nonnegative}, {below_length}")
        self._terminate(f"br i1 {in_range}, label %{ok_label}, label %{fail_label}")
        self._new_block(fail_label)
        self._emit("call void @abort()")
        self._terminate("unreachable")
        self._new_block(ok_label)

    def _emit_nonzero_check(self, divisor: str) -> None:
        nonzero = self._register()
        ok_label = self._fresh_label("div.ok")
        fail_label = self._fresh_label("div.zero")
        self._emit(f"{nonzero} = icmp ne i64 {divisor}, 0")
        self._terminate(f"br i1 {nonzero}, label %{ok_label}, label %{fail_label}")
        self._new_block(fail_label)
        self._emit("call void @abort()")
        self._terminate("unreachable")
        self._new_block(ok_label)

    def _copy_aggregate(self, destination: str, source: str, type_: Type) -> None:
        if isinstance(type_, ArrayType):
            for index in range(type_.length):
                dst = self._register()
                src = self._register()
                llvm_type = self._llvm_type(type_)
                self._emit(f"{dst} = getelementptr inbounds {llvm_type}, ptr {destination}, i64 0, i64 {index}")
                self._emit(f"{src} = getelementptr inbounds {llvm_type}, ptr {source}, i64 0, i64 {index}")
                if self._is_aggregate(type_.element):
                    self._copy_aggregate(dst, src, type_.element)
                else:
                    value = self._register()
                    element_llvm = self._llvm_type(type_.element)
                    align = self._alignment(type_.element)
                    self._emit(f"{value} = load {element_llvm}, ptr {src}, align {align}")
                    self._emit(f"store {element_llvm} {value}, ptr {dst}, align {align}")
            return
        if isinstance(type_, StructType):
            for index, (_, field_type) in enumerate(type_.fields):
                dst = self._register()
                src = self._register()
                llvm_type = self._llvm_type(type_)
                self._emit(f"{dst} = getelementptr inbounds {llvm_type}, ptr {destination}, i32 0, i32 {index}")
                self._emit(f"{src} = getelementptr inbounds {llvm_type}, ptr {source}, i32 0, i32 {index}")
                if self._is_aggregate(field_type):
                    self._copy_aggregate(dst, src, field_type)
                else:
                    value = self._register()
                    field_llvm = self._llvm_type(field_type)
                    align = self._alignment(field_type)
                    self._emit(f"{value} = load {field_llvm}, ptr {src}, align {align}")
                    self._emit(f"store {field_llvm} {value}, ptr {dst}, align {align}")
            return
        raise CodegenError(f"copy requested for non-aggregate type {type_.display()}")

    def _alloca(self, type_: Type, hint: str) -> str:
        name = f"%{self._mangle(hint)}.slot.{self.temp_counter}"
        self.temp_counter += 1
        self.entry_allocas.append(
            f"{name} = alloca {self._llvm_type(type_)}, align {self._alignment(type_)}"
        )
        return name

    def _intern_string(self, value: str) -> tuple[str, int]:
        existing = self.string_globals.get(value)
        if existing is not None:
            return existing
        name = f"@.str.{len(self.string_globals)}"
        length = len(value.encode("utf-8")) + 1
        result = (name, length)
        self.string_globals[value] = result
        self.string_order.append(value)
        return result

    def _new_block(self, label: str) -> _Block:
        block = _Block(label)
        self.blocks.append(block)
        self.current = block
        return block

    def _block(self) -> _Block:
        if self.current is None:
            raise CodegenError("no current basic block")
        return self.current

    def _emit(self, instruction: str) -> None:
        block = self._block()
        if block.terminated:
            raise CodegenError(f"cannot emit after terminator in block {block.label}")
        block.instructions.append(instruction)

    def _terminate(self, instruction: str) -> None:
        self._emit(instruction)
        self._block().terminated = True

    def _register(self) -> str:
        value = f"%r{self.register_counter}"
        self.register_counter += 1
        return value

    def _fresh_label(self, prefix: str) -> str:
        value = f"{prefix}.{self.label_counter}"
        self.label_counter += 1
        return value

    def _llvm_type(self, type_: Type) -> str:
        if type_ == INT:
            return "i64"
        if type_ == BOOL:
            return "i1"
        if type_ == STRING:
            return "ptr"
        if type_ == VOID:
            return "void"
        if isinstance(type_, ArrayType):
            return f"[{type_.length} x {self._llvm_type(type_.element)}]"
        if isinstance(type_, StructType):
            return f"%struct.{self._mangle(type_.name)}"
        if isinstance(type_, FunctionType):
            return "ptr"
        raise CodegenError(f"unsupported type {type_.display()}")

    def _parameter_type(self, type_: Type) -> str:
        return "ptr" if self._is_aggregate(type_) else self._llvm_type(type_)

    @staticmethod
    def _is_aggregate(type_: Type) -> bool:
        return isinstance(type_, (ArrayType, StructType))

    def _alignment(self, type_: Type) -> int:
        if type_ == BOOL:
            return 1
        if type_ in {INT, STRING}:
            return 8
        if isinstance(type_, ArrayType):
            return self._alignment(type_.element)
        if isinstance(type_, StructType):
            return max((self._alignment(field) for _, field in type_.fields), default=1)
        return 8

    @staticmethod
    def _mangle(name: str) -> str:
        output: list[str] = []
        for character in name:
            if character.isalnum() or character in "._":
                output.append(character)
            else:
                output.append(f"_{ord(character):x}_")
        return "".join(output) or "anonymous"

    @staticmethod
    def _escape_identifier(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    @staticmethod
    def _llvm_c_string(value: str) -> str:
        data = value.encode("utf-8") + b"\x00"
        output: list[str] = []
        for byte in data:
            if 32 <= byte <= 126 and byte not in {34, 92}:
                output.append(chr(byte))
            else:
                output.append(f"\\{byte:02X}")
        return "".join(output)
`````

## `code/minilang/minilang/optimizer.py`

`````python
"""Semantics-preserving AST optimization passes used by the teaching compiler."""
from __future__ import annotations

from dataclasses import dataclass

from . import ast


@dataclass(slots=True)
class OptimizationStats:
    constants_folded: int = 0
    branches_removed: int = 0
    statements_removed: int = 0


class AstOptimizer:
    """Apply constant folding, branch simplification, and local dead-code removal."""

    def __init__(self) -> None:
        self.stats = OptimizationStats()

    def optimize(self, program: ast.Program) -> ast.Program:
        declarations: list[ast.Decl] = []
        for declaration in program.declarations:
            if isinstance(declaration, ast.FunctionDecl):
                declarations.append(
                    ast.FunctionDecl(
                        declaration.name,
                        declaration.parameters,
                        declaration.return_type,
                        self._block(declaration.body),
                        declaration.span,
                    )
                )
            else:
                declarations.append(declaration)
        return ast.Program(tuple(declarations), program.span)

    def _block(self, block: ast.BlockStmt) -> ast.BlockStmt:
        statements: list[ast.Stmt] = []
        terminated = False
        for statement in block.statements:
            optimized = self._statement(statement)
            expanded = optimized.statements if isinstance(optimized, _Splice) else (optimized,)
            for item in expanded:
                if terminated:
                    self.stats.statements_removed += 1
                    continue
                statements.append(item)
                if isinstance(item, ast.ReturnStmt):
                    terminated = True
        return ast.BlockStmt(tuple(statements), block.span)

    def _statement(self, statement: ast.Stmt) -> ast.Stmt | "_Splice":
        if isinstance(statement, ast.BlockStmt):
            return self._block(statement)
        if isinstance(statement, ast.LetStmt):
            return ast.LetStmt(statement.name, statement.type_syntax, self._expr(statement.initializer), statement.span)
        if isinstance(statement, ast.ExprStmt):
            return ast.ExprStmt(self._expr(statement.expression), statement.span)
        if isinstance(statement, ast.ReturnStmt):
            value = None if statement.value is None else self._expr(statement.value)
            return ast.ReturnStmt(value, statement.span)
        if isinstance(statement, ast.IfStmt):
            condition = self._expr(statement.condition)
            then_branch = self._block(statement.then_branch)
            if isinstance(statement.else_branch, ast.BlockStmt):
                else_branch: ast.BlockStmt | ast.IfStmt | None = self._block(statement.else_branch)
            elif isinstance(statement.else_branch, ast.IfStmt):
                nested = self._statement(statement.else_branch)
                assert isinstance(nested, ast.IfStmt)
                else_branch = nested
            else:
                else_branch = None
            if isinstance(condition, ast.BooleanExpr):
                self.stats.branches_removed += 1
                selected = then_branch if condition.value else else_branch
                if selected is None:
                    return _Splice(())
                if isinstance(selected, ast.BlockStmt):
                    return _Splice(selected.statements)
                return selected
            return ast.IfStmt(condition, then_branch, else_branch, statement.span)
        if isinstance(statement, ast.WhileStmt):
            condition = self._expr(statement.condition)
            body = self._block(statement.body)
            if isinstance(condition, ast.BooleanExpr) and not condition.value:
                self.stats.branches_removed += 1
                return _Splice(())
            return ast.WhileStmt(condition, body, statement.span)
        if isinstance(statement, ast.ForStmt):
            initializer = None
            if statement.initializer is not None:
                initializer_result = self._statement(statement.initializer)
                if isinstance(initializer_result, _Splice):
                    initializer = initializer_result.statements[0] if initializer_result.statements else None
                else:
                    initializer = initializer_result
            condition = None if statement.condition is None else self._expr(statement.condition)
            increment = None if statement.increment is None else self._expr(statement.increment)
            body = self._block(statement.body)
            if isinstance(condition, ast.BooleanExpr) and not condition.value:
                self.stats.branches_removed += 1
                return _Splice(() if initializer is None else (initializer,))
            return ast.ForStmt(initializer, condition, increment, body, statement.span)
        raise AssertionError(f"unhandled statement {type(statement).__name__}")

    def _expr(self, expression: ast.Expr) -> ast.Expr:
        if isinstance(expression, (ast.IntegerExpr, ast.BooleanExpr, ast.StringExpr, ast.NameExpr, ast.ErrorExpr)):
            return expression
        if isinstance(expression, ast.ArrayExpr):
            return ast.ArrayExpr(tuple(self._expr(item) for item in expression.elements), expression.span)
        if isinstance(expression, ast.StructInitExpr):
            fields = tuple(
                ast.StructInitField(field.name, self._expr(field.value), field.span)
                for field in expression.fields
            )
            return ast.StructInitExpr(expression.name, fields, expression.span)
        if isinstance(expression, ast.UnaryExpr):
            operand = self._expr(expression.operand)
            result: ast.Expr | None = None
            if expression.operator == "-" and isinstance(operand, ast.IntegerExpr):
                result = ast.IntegerExpr(-operand.value, expression.span)
            elif expression.operator == "+" and isinstance(operand, ast.IntegerExpr):
                result = ast.IntegerExpr(operand.value, expression.span)
            elif expression.operator == "!" and isinstance(operand, ast.BooleanExpr):
                result = ast.BooleanExpr(not operand.value, expression.span)
            if result is not None:
                self.stats.constants_folded += 1
                return result
            return ast.UnaryExpr(expression.operator, operand, expression.span)
        if isinstance(expression, ast.BinaryExpr):
            left = self._expr(expression.left)
            # Preserve short-circuit semantics while simplifying known left values.
            if expression.operator == "&&" and isinstance(left, ast.BooleanExpr):
                self.stats.constants_folded += 1
                return self._expr(expression.right) if left.value else ast.BooleanExpr(False, expression.span)
            if expression.operator == "||" and isinstance(left, ast.BooleanExpr):
                self.stats.constants_folded += 1
                return ast.BooleanExpr(True, expression.span) if left.value else self._expr(expression.right)
            right = self._expr(expression.right)
            result = self._fold_binary(expression.operator, left, right, expression.span)
            if result is not None:
                self.stats.constants_folded += 1
                return result
            return ast.BinaryExpr(left, expression.operator, right, expression.span)
        if isinstance(expression, ast.AssignExpr):
            return ast.AssignExpr(expression.target, self._expr(expression.value), expression.span)
        if isinstance(expression, ast.CallExpr):
            return ast.CallExpr(self._expr(expression.callee), tuple(self._expr(a) for a in expression.arguments), expression.span)
        if isinstance(expression, ast.IndexExpr):
            collection = self._expr(expression.collection)
            index = self._expr(expression.index)
            if isinstance(collection, ast.ArrayExpr) and isinstance(index, ast.IntegerExpr):
                if 0 <= index.value < len(collection.elements):
                    self.stats.constants_folded += 1
                    return collection.elements[index.value]
            return ast.IndexExpr(collection, index, expression.span)
        if isinstance(expression, ast.FieldExpr):
            receiver = self._expr(expression.receiver)
            if isinstance(receiver, ast.StructInitExpr):
                for field in receiver.fields:
                    if field.name == expression.name:
                        self.stats.constants_folded += 1
                        return field.value
            return ast.FieldExpr(receiver, expression.name, expression.span)
        raise AssertionError(f"unhandled expression {type(expression).__name__}")

    @staticmethod
    def _fold_binary(operator: str, left: ast.Expr, right: ast.Expr, span) -> ast.Expr | None:
        if isinstance(left, ast.IntegerExpr) and isinstance(right, ast.IntegerExpr):
            a, b = left.value, right.value
            if operator == "+":
                return ast.IntegerExpr(a + b, span)
            if operator == "-":
                return ast.IntegerExpr(a - b, span)
            if operator == "*":
                return ast.IntegerExpr(a * b, span)
            if operator == "/" and b != 0:
                q = abs(a) // abs(b)
                return ast.IntegerExpr(-q if (a < 0) ^ (b < 0) else q, span)
            if operator == "%" and b != 0:
                q = abs(a) // abs(b)
                q = -q if (a < 0) ^ (b < 0) else q
                return ast.IntegerExpr(a - q * b, span)
            if operator == "<":
                return ast.BooleanExpr(a < b, span)
            if operator == "<=":
                return ast.BooleanExpr(a <= b, span)
            if operator == ">":
                return ast.BooleanExpr(a > b, span)
            if operator == ">=":
                return ast.BooleanExpr(a >= b, span)
            if operator == "==":
                return ast.BooleanExpr(a == b, span)
            if operator == "!=":
                return ast.BooleanExpr(a != b, span)
        if isinstance(left, ast.BooleanExpr) and isinstance(right, ast.BooleanExpr):
            if operator == "==":
                return ast.BooleanExpr(left.value == right.value, span)
            if operator == "!=":
                return ast.BooleanExpr(left.value != right.value, span)
        if isinstance(left, ast.StringExpr) and isinstance(right, ast.StringExpr):
            if operator == "==":
                return ast.BooleanExpr(left.value == right.value, span)
            if operator == "!=":
                return ast.BooleanExpr(left.value != right.value, span)
        return None


@dataclass(frozen=True, slots=True)
class _Splice:
    statements: tuple[ast.Stmt, ...]
`````

## `code/minilang/minilang/parser.py`

`````python
"""Recursive-descent and precedence-climbing parser for MiniLang."""
from __future__ import annotations

from . import ast
from .diagnostics import DiagnosticBag
from .token import SourceSpan, Token, TokenKind


class Parser:
    def __init__(self, tokens: tuple[Token, ...]) -> None:
        self.tokens = tokens
        self.index = 0
        self.diagnostics = DiagnosticBag()

    def parse_program(self) -> ast.Program:
        declarations: list[ast.Decl] = []
        start = self.current.span
        while not self._check(TokenKind.EOF):
            before = self.index
            declaration = self._parse_declaration()
            if declaration is not None:
                declarations.append(declaration)
            if self.index == before:
                self._advance()
        end = self.current.span
        return ast.Program(tuple(declarations), SourceSpan.covering(start, end))

    @property
    def current(self) -> Token:
        return self.tokens[min(self.index, len(self.tokens) - 1)]

    @property
    def previous(self) -> Token:
        return self.tokens[max(0, self.index - 1)]

    def _parse_declaration(self) -> ast.Decl | None:
        if self._match(TokenKind.STRUCT):
            return self._parse_struct_declaration(self.previous)
        if self._match(TokenKind.FN):
            return self._parse_function_declaration(self.previous)
        self._error(self.current, "PAR001", "top-level declaration must start with 'struct' or 'fn'")
        self._synchronize_declaration()
        return None

    def _parse_struct_declaration(self, start: Token) -> ast.StructDecl:
        name = self._expect(TokenKind.IDENTIFIER, "PAR002", "expected structure name")
        self._expect(TokenKind.LEFT_BRACE, "PAR003", "expected '{' after structure name")
        fields: list[ast.StructField] = []
        seen: set[str] = set()
        while not self._check(TokenKind.RIGHT_BRACE) and not self._check(TokenKind.EOF):
            field_name = self._expect(TokenKind.IDENTIFIER, "PAR004", "expected field name")
            self._expect(TokenKind.COLON, "PAR005", "expected ':' after field name")
            type_syntax = self._parse_type()
            semi = self._expect(TokenKind.SEMICOLON, "PAR006", "expected ';' after field declaration")
            if field_name.lexeme in seen:
                self._error(field_name, "PAR007", f"duplicate field {field_name.lexeme!r}")
            seen.add(field_name.lexeme)
            fields.append(
                ast.StructField(
                    field_name.lexeme,
                    type_syntax,
                    SourceSpan.covering(field_name.span, semi.span),
                )
            )
        close = self._expect(TokenKind.RIGHT_BRACE, "PAR008", "expected '}' after structure declaration")
        return ast.StructDecl(name.lexeme, tuple(fields), SourceSpan.covering(start.span, close.span))

    def _parse_function_declaration(self, start: Token) -> ast.FunctionDecl:
        name = self._expect(TokenKind.IDENTIFIER, "PAR009", "expected function name")
        self._expect(TokenKind.LEFT_PAREN, "PAR010", "expected '(' after function name")
        parameters: list[ast.Parameter] = []
        if not self._check(TokenKind.RIGHT_PAREN):
            while True:
                param_name = self._expect(TokenKind.IDENTIFIER, "PAR011", "expected parameter name")
                self._expect(TokenKind.COLON, "PAR012", "expected ':' after parameter name")
                type_syntax = self._parse_type()
                parameters.append(
                    ast.Parameter(
                        param_name.lexeme,
                        type_syntax,
                        SourceSpan.covering(param_name.span, type_syntax.span),
                    )
                )
                if not self._match(TokenKind.COMMA):
                    break
        self._expect(TokenKind.RIGHT_PAREN, "PAR013", "expected ')' after parameters")
        if self._match(TokenKind.ARROW):
            return_type = self._parse_type()
        else:
            token = self.previous
            return_type = ast.TypeSyntax(token.span, name="void")
        body = self._parse_block()
        return ast.FunctionDecl(
            name.lexeme,
            tuple(parameters),
            return_type,
            body,
            SourceSpan.covering(start.span, body.span),
        )

    def _parse_type(self) -> ast.TypeSyntax:
        if self._match(TokenKind.LEFT_BRACKET):
            start = self.previous
            element = self._parse_type()
            self._expect(TokenKind.SEMICOLON, "PAR014", "expected ';' between array element type and length")
            length_token = self._expect(TokenKind.INTEGER, "PAR015", "expected array length")
            close = self._expect(TokenKind.RIGHT_BRACKET, "PAR016", "expected ']' after array type")
            length = int(length_token.literal) if isinstance(length_token.literal, int) else 0
            if length <= 0:
                self._error(length_token, "PAR017", "array length must be positive")
            return ast.TypeSyntax(SourceSpan.covering(start.span, close.span), element=element, length=max(0, length))

        names = {
            TokenKind.INT: "int",
            TokenKind.BOOL: "bool",
            TokenKind.STRING_TYPE: "string",
            TokenKind.VOID: "void",
        }
        if self.current.kind in names:
            token = self._advance()
            return ast.TypeSyntax(token.span, name=names[token.kind])
        if self._match(TokenKind.IDENTIFIER):
            token = self.previous
            return ast.TypeSyntax(token.span, name=token.lexeme)
        token = self.current
        self._error(token, "PAR018", "expected a type")
        self._advance_if_not_eof()
        return ast.TypeSyntax(token.span, name="<error>")

    def _parse_block(self) -> ast.BlockStmt:
        open_brace = self._expect(TokenKind.LEFT_BRACE, "PAR019", "expected '{' to start block")
        statements: list[ast.Stmt] = []
        while not self._check(TokenKind.RIGHT_BRACE) and not self._check(TokenKind.EOF):
            before = self.index
            statements.append(self._parse_statement())
            if self.index == before:
                self._advance()
        close = self._expect(TokenKind.RIGHT_BRACE, "PAR020", "expected '}' after block")
        return ast.BlockStmt(tuple(statements), SourceSpan.covering(open_brace.span, close.span))

    def _parse_statement(self) -> ast.Stmt:
        if self._match(TokenKind.LET):
            return self._parse_let_statement(self.previous)
        if self._match(TokenKind.IF):
            return self._parse_if_statement(self.previous)
        if self._match(TokenKind.WHILE):
            return self._parse_while_statement(self.previous)
        if self._match(TokenKind.FOR):
            return self._parse_for_statement(self.previous)
        if self._match(TokenKind.RETURN):
            return self._parse_return_statement(self.previous)
        if self._check(TokenKind.LEFT_BRACE):
            return self._parse_block()
        expression = self._parse_expression()
        semi = self._expect(TokenKind.SEMICOLON, "PAR021", "expected ';' after expression")
        return ast.ExprStmt(expression, SourceSpan.covering(expression.span, semi.span))

    def _parse_let_statement(self, start: Token) -> ast.LetStmt:
        name = self._expect(TokenKind.IDENTIFIER, "PAR022", "expected variable name")
        type_syntax: ast.TypeSyntax | None = None
        if self._match(TokenKind.COLON):
            type_syntax = self._parse_type()
        self._expect(TokenKind.EQUAL, "PAR023", "expected '=' in variable declaration")
        initializer = self._parse_expression()
        semi = self._expect(TokenKind.SEMICOLON, "PAR024", "expected ';' after variable declaration")
        return ast.LetStmt(name.lexeme, type_syntax, initializer, SourceSpan.covering(start.span, semi.span))

    def _parse_if_statement(self, start: Token) -> ast.IfStmt:
        self._expect(TokenKind.LEFT_PAREN, "PAR025", "expected '(' after 'if'")
        condition = self._parse_expression()
        self._expect(TokenKind.RIGHT_PAREN, "PAR026", "expected ')' after if condition")
        then_branch = self._parse_block()
        else_branch: ast.BlockStmt | ast.IfStmt | None = None
        if self._match(TokenKind.ELSE):
            if self._match(TokenKind.IF):
                else_branch = self._parse_if_statement(self.previous)
            else:
                else_branch = self._parse_block()
        end_span = else_branch.span if else_branch is not None else then_branch.span
        return ast.IfStmt(condition, then_branch, else_branch, SourceSpan.covering(start.span, end_span))

    def _parse_while_statement(self, start: Token) -> ast.WhileStmt:
        self._expect(TokenKind.LEFT_PAREN, "PAR027", "expected '(' after 'while'")
        condition = self._parse_expression()
        self._expect(TokenKind.RIGHT_PAREN, "PAR028", "expected ')' after while condition")
        body = self._parse_block()
        return ast.WhileStmt(condition, body, SourceSpan.covering(start.span, body.span))

    def _parse_for_statement(self, start: Token) -> ast.ForStmt:
        self._expect(TokenKind.LEFT_PAREN, "PAR029", "expected '(' after 'for'")
        initializer: ast.Stmt | None
        if self._match(TokenKind.SEMICOLON):
            initializer = None
        elif self._match(TokenKind.LET):
            initializer = self._parse_let_statement(self.previous)
        else:
            expression = self._parse_expression()
            semi = self._expect(TokenKind.SEMICOLON, "PAR030", "expected ';' after for initializer")
            initializer = ast.ExprStmt(expression, SourceSpan.covering(expression.span, semi.span))

        condition = None if self._check(TokenKind.SEMICOLON) else self._parse_expression()
        self._expect(TokenKind.SEMICOLON, "PAR031", "expected ';' after for condition")
        increment = None if self._check(TokenKind.RIGHT_PAREN) else self._parse_expression()
        self._expect(TokenKind.RIGHT_PAREN, "PAR032", "expected ')' after for clauses")
        body = self._parse_block()
        return ast.ForStmt(initializer, condition, increment, body, SourceSpan.covering(start.span, body.span))

    def _parse_return_statement(self, start: Token) -> ast.ReturnStmt:
        value = None if self._check(TokenKind.SEMICOLON) else self._parse_expression()
        semi = self._expect(TokenKind.SEMICOLON, "PAR033", "expected ';' after return statement")
        return ast.ReturnStmt(value, SourceSpan.covering(start.span, semi.span))

    def _parse_expression(self) -> ast.Expr:
        return self._parse_assignment()

    def _parse_assignment(self) -> ast.Expr:
        left = self._parse_or()
        if self._match(TokenKind.EQUAL):
            value = self._parse_assignment()
            if not isinstance(left, (ast.NameExpr, ast.IndexExpr, ast.FieldExpr)):
                self._error(self.previous, "PAR034", "invalid assignment target")
            return ast.AssignExpr(left, value, SourceSpan.covering(left.span, value.span))
        return left

    def _parse_or(self) -> ast.Expr:
        expression = self._parse_and()
        while self._match(TokenKind.OR_OR):
            operator = self.previous
            right = self._parse_and()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_and(self) -> ast.Expr:
        expression = self._parse_equality()
        while self._match(TokenKind.AND_AND):
            operator = self.previous
            right = self._parse_equality()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_equality(self) -> ast.Expr:
        expression = self._parse_comparison()
        while self._match(TokenKind.EQUAL_EQUAL, TokenKind.BANG_EQUAL):
            operator = self.previous
            right = self._parse_comparison()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_comparison(self) -> ast.Expr:
        expression = self._parse_term()
        while self._match(TokenKind.LESS, TokenKind.LESS_EQUAL, TokenKind.GREATER, TokenKind.GREATER_EQUAL):
            operator = self.previous
            right = self._parse_term()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_term(self) -> ast.Expr:
        expression = self._parse_factor()
        while self._match(TokenKind.PLUS, TokenKind.MINUS):
            operator = self.previous
            right = self._parse_factor()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_factor(self) -> ast.Expr:
        expression = self._parse_unary()
        while self._match(TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT):
            operator = self.previous
            right = self._parse_unary()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_unary(self) -> ast.Expr:
        if self._match(TokenKind.BANG, TokenKind.MINUS, TokenKind.PLUS):
            operator = self.previous
            operand = self._parse_unary()
            return ast.UnaryExpr(operator.lexeme, operand, SourceSpan.covering(operator.span, operand.span))
        return self._parse_postfix()

    def _parse_postfix(self) -> ast.Expr:
        expression = self._parse_primary()
        while True:
            if self._match(TokenKind.LEFT_PAREN):
                arguments: list[ast.Expr] = []
                if not self._check(TokenKind.RIGHT_PAREN):
                    while True:
                        arguments.append(self._parse_expression())
                        if not self._match(TokenKind.COMMA):
                            break
                close = self._expect(TokenKind.RIGHT_PAREN, "PAR035", "expected ')' after arguments")
                expression = ast.CallExpr(expression, tuple(arguments), SourceSpan.covering(expression.span, close.span))
            elif self._match(TokenKind.LEFT_BRACKET):
                index = self._parse_expression()
                close = self._expect(TokenKind.RIGHT_BRACKET, "PAR036", "expected ']' after index")
                expression = ast.IndexExpr(expression, index, SourceSpan.covering(expression.span, close.span))
            elif self._match(TokenKind.DOT):
                name = self._expect(TokenKind.IDENTIFIER, "PAR037", "expected field name after '.'")
                expression = ast.FieldExpr(expression, name.lexeme, SourceSpan.covering(expression.span, name.span))
            else:
                break
        return expression

    def _parse_primary(self) -> ast.Expr:
        if self._match(TokenKind.INTEGER):
            token = self.previous
            return ast.IntegerExpr(int(token.literal), token.span)
        if self._match(TokenKind.STRING):
            token = self.previous
            return ast.StringExpr(str(token.literal), token.span)
        if self._match(TokenKind.TRUE):
            return ast.BooleanExpr(True, self.previous.span)
        if self._match(TokenKind.FALSE):
            return ast.BooleanExpr(False, self.previous.span)
        if self._match(TokenKind.LEFT_PAREN):
            open_token = self.previous
            expression = self._parse_expression()
            close = self._expect(TokenKind.RIGHT_PAREN, "PAR038", "expected ')' after expression")
            # Parentheses do not need a separate AST node, but their span is
            # intentionally not discarded from diagnostics at this level.
            _ = SourceSpan.covering(open_token.span, close.span)
            return expression
        if self._match(TokenKind.LEFT_BRACKET):
            open_token = self.previous
            elements: list[ast.Expr] = []
            if not self._check(TokenKind.RIGHT_BRACKET):
                while True:
                    elements.append(self._parse_expression())
                    if not self._match(TokenKind.COMMA):
                        break
            close = self._expect(TokenKind.RIGHT_BRACKET, "PAR039", "expected ']' after array literal")
            return ast.ArrayExpr(tuple(elements), SourceSpan.covering(open_token.span, close.span))
        if self._match(TokenKind.IDENTIFIER):
            name = self.previous
            if self._match(TokenKind.LEFT_BRACE):
                fields: list[ast.StructInitField] = []
                if not self._check(TokenKind.RIGHT_BRACE):
                    while True:
                        field_name = self._expect(TokenKind.IDENTIFIER, "PAR040", "expected field name")
                        self._expect(TokenKind.COLON, "PAR041", "expected ':' after field name")
                        value = self._parse_expression()
                        fields.append(
                            ast.StructInitField(
                                field_name.lexeme,
                                value,
                                SourceSpan.covering(field_name.span, value.span),
                            )
                        )
                        if not self._match(TokenKind.COMMA):
                            break
                close = self._expect(TokenKind.RIGHT_BRACE, "PAR042", "expected '}' after structure initializer")
                return ast.StructInitExpr(name.lexeme, tuple(fields), SourceSpan.covering(name.span, close.span))
            return ast.NameExpr(name.lexeme, name.span)

        token = self.current
        self._error(token, "PAR043", f"expected expression, found {token.kind.name}")
        self._advance_if_not_eof()
        return ast.ErrorExpr(token.span)

    def _expect(self, kind: TokenKind, code: str, message: str) -> Token:
        if self._check(kind):
            return self._advance()
        self._error(self.current, code, message)
        # Synthetic zero-width token anchors recovery at the current location.
        return Token(kind, "", None, self.current.span)

    def _error(self, token: Token, code: str, message: str) -> None:
        self.diagnostics.error(code, message, token.span)

    def _synchronize_declaration(self) -> None:
        while not self._check(TokenKind.EOF):
            if self.current.kind in {TokenKind.FN, TokenKind.STRUCT}:
                return
            self._advance()

    def _advance_if_not_eof(self) -> None:
        if not self._check(TokenKind.EOF):
            self._advance()

    def _match(self, *kinds: TokenKind) -> bool:
        if self.current.kind not in kinds:
            return False
        self._advance()
        return True

    def _check(self, kind: TokenKind) -> bool:
        return self.current.kind is kind

    def _advance(self) -> Token:
        token = self.current
        if token.kind is not TokenKind.EOF:
            self.index += 1
        return token
`````

## `code/minilang/minilang/semantic.py`

`````python
"""Name resolution and static type checking for MiniLang."""
from __future__ import annotations

from dataclasses import dataclass

from . import ast
from .diagnostics import DiagnosticBag
from .symbols import (
    BuiltinSymbol,
    FunctionSymbol,
    Scope,
    StructSymbol,
    Symbol,
    SymbolKind,
    VariableSymbol,
)
from .typesys import (
    ArrayType,
    BOOL,
    ERROR,
    INT,
    STRING,
    VOID,
    FunctionType,
    StructType,
    Type,
    is_assignable,
    same_type,
)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    diagnostics: tuple
    node_types: dict[int, Type]
    bindings: dict[int, Symbol]
    declarations: dict[int, Symbol]
    functions: dict[str, FunctionSymbol]
    structs: dict[str, StructSymbol]

    def type_of(self, node: ast.Node) -> Type:
        return self.node_types.get(id(node), ERROR)

    def binding_of(self, node: ast.Node) -> Symbol | None:
        return self.bindings.get(id(node))


class SemanticAnalyzer:
    def __init__(self, program: ast.Program) -> None:
        self.program = program
        self.diagnostics = DiagnosticBag()
        self.node_types: dict[int, Type] = {}
        self.bindings: dict[int, Symbol] = {}
        self.declarations: dict[int, Symbol] = {}
        self.functions: dict[str, FunctionSymbol] = {}
        self.structs: dict[str, StructSymbol] = {}
        self.struct_declarations: dict[str, ast.StructDecl] = {}
        self.struct_states: dict[str, str] = {}
        self.global_scope = Scope()
        self.scope = self.global_scope
        self.current_function: FunctionSymbol | None = None
        self._install_builtins()

    def analyze(self) -> AnalysisResult:
        self._collect_struct_names()
        self._resolve_structs()
        self._collect_functions()
        for declaration in self.program.declarations:
            if isinstance(declaration, ast.FunctionDecl):
                symbol = self.functions.get(declaration.name)
                if symbol is not None and symbol.declaration is declaration:
                    self._analyze_function(declaration, symbol)
        return AnalysisResult(
            self.diagnostics.items,
            dict(self.node_types),
            dict(self.bindings),
            dict(self.declarations),
            dict(self.functions),
            dict(self.structs),
        )

    def _install_builtins(self) -> None:
        builtins: tuple[tuple[str, FunctionType | None], ...] = (
            ("print_int", FunctionType((INT,), VOID)),
            ("print_bool", FunctionType((BOOL,), VOID)),
            ("print_string", FunctionType((STRING,), VOID)),
            ("assert", FunctionType((BOOL,), VOID)),
            # len is intentionally overloaded and checked specially.
            ("len", None),
        )
        for name, function_type in builtins:
            self.global_scope.define(BuiltinSymbol(name, SymbolKind.BUILTIN, function_type))

    def _collect_struct_names(self) -> None:
        for declaration in self.program.declarations:
            if not isinstance(declaration, ast.StructDecl):
                continue
            if declaration.name in self.struct_declarations or self.global_scope.lookup_local(declaration.name):
                self.diagnostics.error(
                    "SEM001",
                    f"duplicate top-level name {declaration.name!r}",
                    declaration.span,
                )
                continue
            self.struct_declarations[declaration.name] = declaration
            self.struct_states[declaration.name] = "unresolved"

    def _resolve_structs(self) -> None:
        for name in tuple(self.struct_declarations):
            self._resolve_struct(name)
        for name, symbol in self.structs.items():
            self.global_scope.define(symbol)

    def _resolve_struct(self, name: str) -> StructType:
        existing = self.structs.get(name)
        if existing is not None:
            return existing.type
        state = self.struct_states.get(name)
        declaration = self.struct_declarations.get(name)
        if declaration is None:
            return ERROR  # type: ignore[return-value]
        if state == "resolving":
            self.diagnostics.error(
                "SEM002",
                f"recursive by-value structure {name!r} has infinite size",
                declaration.span,
            )
            return StructType(name, ())

        self.struct_states[name] = "resolving"
        fields: list[tuple[str, Type]] = []
        for field in declaration.fields:
            field_type = self._resolve_type_syntax(field.type_syntax, resolving_struct=name)
            if field_type == VOID:
                self.diagnostics.error("SEM003", "structure field cannot have type void", field.span)
                field_type = ERROR
            fields.append((field.name, field_type))
        type_ = StructType(name, tuple(fields))
        symbol = StructSymbol(name, SymbolKind.STRUCT, type_, declaration)
        self.structs[name] = symbol
        self.declarations[id(declaration)] = symbol
        self.struct_states[name] = "resolved"
        return type_

    def _collect_functions(self) -> None:
        for declaration in self.program.declarations:
            if not isinstance(declaration, ast.FunctionDecl):
                continue
            if self.global_scope.lookup_local(declaration.name) is not None:
                self.diagnostics.error(
                    "SEM004",
                    f"duplicate top-level name {declaration.name!r}",
                    declaration.span,
                )
                continue
            parameter_types = tuple(self._resolve_type_syntax(p.type_syntax) for p in declaration.parameters)
            return_type = self._resolve_type_syntax(declaration.return_type)
            if isinstance(return_type, (ArrayType, StructType)):
                self.diagnostics.error(
                    "SEM040",
                    "MiniLang 1.0 functions return only int, bool, string, or void; pass aggregates by value as parameters",
                    declaration.return_type.span,
                )
            if any(type_ == VOID for type_ in parameter_types):
                self.diagnostics.error("SEM005", "parameter cannot have type void", declaration.span)
            function_type = FunctionType(parameter_types, return_type)
            symbol = FunctionSymbol(declaration.name, SymbolKind.FUNCTION, function_type, declaration)
            self.functions[declaration.name] = symbol
            self.declarations[id(declaration)] = symbol
            self.global_scope.define(symbol)

        main = self.functions.get("main")
        if main is None:
            self.diagnostics.error("SEM006", "program must define fn main() -> int", self.program.span)
        elif main.type.parameters or main.type.return_type != INT:
            self.diagnostics.error("SEM007", "main must have type fn() -> int", main.declaration.span)

    def _analyze_function(self, declaration: ast.FunctionDecl, symbol: FunctionSymbol) -> None:
        previous_function = self.current_function
        previous_scope = self.scope
        self.current_function = symbol
        self.scope = Scope(self.global_scope)
        seen: set[str] = set()
        for parameter, parameter_type in zip(declaration.parameters, symbol.type.parameters):
            if parameter.name in seen:
                self.diagnostics.error("SEM008", f"duplicate parameter {parameter.name!r}", parameter.span)
                continue
            seen.add(parameter.name)
            parameter_symbol = VariableSymbol(
                parameter.name,
                SymbolKind.PARAMETER,
                parameter_type,
                mutable=True,
                depth=self.scope.depth,
            )
            self.scope.define(parameter_symbol)
            self.declarations[id(parameter)] = parameter_symbol
        self._analyze_block(declaration.body, create_scope=False)
        if symbol.type.return_type != VOID and not self._always_returns(declaration.body):
            self.diagnostics.error(
                "SEM009",
                f"function {declaration.name!r} may reach the end without returning {symbol.type.return_type.display()}",
                declaration.body.span,
            )
        self.scope = previous_scope
        self.current_function = previous_function

    def _analyze_block(self, block: ast.BlockStmt, create_scope: bool = True) -> None:
        previous = self.scope
        if create_scope:
            self.scope = Scope(previous)
        for statement in block.statements:
            self._analyze_statement(statement)
        if create_scope:
            self.scope = previous

    def _analyze_statement(self, statement: ast.Stmt) -> None:
        if isinstance(statement, ast.BlockStmt):
            self._analyze_block(statement)
        elif isinstance(statement, ast.LetStmt):
            value_type = self._analyze_expression(statement.initializer)
            declared_type = (
                self._resolve_type_syntax(statement.type_syntax)
                if statement.type_syntax is not None
                else value_type
            )
            if declared_type == VOID:
                self.diagnostics.error("SEM010", "variable cannot have type void", statement.span)
                declared_type = ERROR
            if not is_assignable(declared_type, value_type):
                self.diagnostics.error(
                    "SEM011",
                    f"cannot initialize {statement.name!r} of type {declared_type.display()} "
                    f"with {value_type.display()}",
                    statement.initializer.span,
                )
            symbol = VariableSymbol(
                statement.name,
                SymbolKind.VARIABLE,
                declared_type,
                mutable=True,
                depth=self.scope.depth,
            )
            if not self.scope.define(symbol):
                self.diagnostics.error(
                    "SEM012",
                    f"name {statement.name!r} is already declared in this scope",
                    statement.span,
                )
            self.declarations[id(statement)] = symbol
        elif isinstance(statement, ast.ExprStmt):
            self._analyze_expression(statement.expression)
        elif isinstance(statement, ast.IfStmt):
            self._require_bool(statement.condition, "if condition")
            self._analyze_block(statement.then_branch)
            if isinstance(statement.else_branch, ast.BlockStmt):
                self._analyze_block(statement.else_branch)
            elif isinstance(statement.else_branch, ast.IfStmt):
                self._analyze_statement(statement.else_branch)
        elif isinstance(statement, ast.WhileStmt):
            self._require_bool(statement.condition, "while condition")
            self._analyze_block(statement.body)
        elif isinstance(statement, ast.ForStmt):
            previous = self.scope
            self.scope = Scope(previous)
            if statement.initializer is not None:
                self._analyze_statement(statement.initializer)
            if statement.condition is not None:
                self._require_bool(statement.condition, "for condition")
            if statement.increment is not None:
                self._analyze_expression(statement.increment)
            self._analyze_block(statement.body)
            self.scope = previous
        elif isinstance(statement, ast.ReturnStmt):
            assert self.current_function is not None
            expected = self.current_function.type.return_type
            actual = VOID if statement.value is None else self._analyze_expression(statement.value)
            if not is_assignable(expected, actual):
                self.diagnostics.error(
                    "SEM013",
                    f"return type mismatch: expected {expected.display()}, got {actual.display()}",
                    statement.span,
                )
        else:
            raise AssertionError(f"unhandled statement: {type(statement).__name__}")

    def _analyze_expression(self, expression: ast.Expr) -> Type:
        if isinstance(expression, ast.IntegerExpr):
            return self._record_type(expression, INT)
        if isinstance(expression, ast.BooleanExpr):
            return self._record_type(expression, BOOL)
        if isinstance(expression, ast.StringExpr):
            return self._record_type(expression, STRING)
        if isinstance(expression, ast.ErrorExpr):
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.NameExpr):
            symbol = self.scope.lookup(expression.name)
            if symbol is None:
                self.diagnostics.error("SEM014", f"undefined name {expression.name!r}", expression.span)
                return self._record_type(expression, ERROR)
            self.bindings[id(expression)] = symbol
            if isinstance(symbol, VariableSymbol):
                return self._record_type(expression, symbol.type)
            if isinstance(symbol, (FunctionSymbol, BuiltinSymbol)):
                return self._record_type(expression, symbol.type or ERROR)
            self.diagnostics.error("SEM015", f"{expression.name!r} is a type, not a value", expression.span)
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.ArrayExpr):
            if not expression.elements:
                self.diagnostics.error(
                    "SEM016",
                    "cannot infer the type of an empty array literal; add an explicit variable type",
                    expression.span,
                )
                return self._record_type(expression, ArrayType(ERROR, 0))
            element_type = self._analyze_expression(expression.elements[0])
            for element in expression.elements[1:]:
                current = self._analyze_expression(element)
                if not same_type(element_type, current):
                    self.diagnostics.error(
                        "SEM017",
                        f"array element has type {current.display()}, expected {element_type.display()}",
                        element.span,
                    )
            return self._record_type(expression, ArrayType(element_type, len(expression.elements)))
        if isinstance(expression, ast.StructInitExpr):
            symbol = self.structs.get(expression.name)
            if symbol is None:
                self.diagnostics.error("SEM018", f"unknown structure {expression.name!r}", expression.span)
                for field in expression.fields:
                    self._analyze_expression(field.value)
                return self._record_type(expression, ERROR)
            supplied: dict[str, ast.StructInitField] = {}
            for field in expression.fields:
                if field.name in supplied:
                    self.diagnostics.error("SEM019", f"duplicate initializer for field {field.name!r}", field.span)
                supplied[field.name] = field
            for name, expected in symbol.type.fields:
                field = supplied.pop(name, None)
                if field is None:
                    self.diagnostics.error("SEM020", f"missing initializer for field {name!r}", expression.span)
                    continue
                actual = self._analyze_expression(field.value)
                if not is_assignable(expected, actual):
                    self.diagnostics.error(
                        "SEM021",
                        f"field {name!r} expects {expected.display()}, got {actual.display()}",
                        field.value.span,
                    )
            for unknown in supplied.values():
                self.diagnostics.error("SEM022", f"unknown field {unknown.name!r}", unknown.span)
                self._analyze_expression(unknown.value)
            self.bindings[id(expression)] = symbol
            return self._record_type(expression, symbol.type)
        if isinstance(expression, ast.UnaryExpr):
            operand = self._analyze_expression(expression.operand)
            if expression.operator in {"-", "+"}:
                self._expect_type(operand, INT, expression.operand, f"operator {expression.operator}")
                return self._record_type(expression, INT)
            if expression.operator == "!":
                self._expect_type(operand, BOOL, expression.operand, "operator !")
                return self._record_type(expression, BOOL)
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.BinaryExpr):
            left = self._analyze_expression(expression.left)
            right = self._analyze_expression(expression.right)
            op = expression.operator
            if op in {"+", "-", "*", "/", "%"}:
                self._expect_type(left, INT, expression.left, f"left operand of {op}")
                self._expect_type(right, INT, expression.right, f"right operand of {op}")
                return self._record_type(expression, INT)
            if op in {"<", "<=", ">", ">="}:
                self._expect_type(left, INT, expression.left, f"left operand of {op}")
                self._expect_type(right, INT, expression.right, f"right operand of {op}")
                return self._record_type(expression, BOOL)
            if op in {"&&", "||"}:
                self._expect_type(left, BOOL, expression.left, f"left operand of {op}")
                self._expect_type(right, BOOL, expression.right, f"right operand of {op}")
                return self._record_type(expression, BOOL)
            if op in {"==", "!="}:
                if not same_type(left, right):
                    self.diagnostics.error(
                        "SEM023",
                        f"cannot compare {left.display()} with {right.display()}",
                        expression.span,
                    )
                if not (left.is_scalar or left.is_error):
                    self.diagnostics.error("SEM024", "aggregate equality is not supported", expression.span)
                return self._record_type(expression, BOOL)
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.AssignExpr):
            target_type = self._analyze_lvalue(expression.target)
            value_type = self._analyze_expression(expression.value)
            if not is_assignable(target_type, value_type):
                self.diagnostics.error(
                    "SEM025",
                    f"cannot assign {value_type.display()} to {target_type.display()}",
                    expression.span,
                )
            return self._record_type(expression, target_type)
        if isinstance(expression, ast.CallExpr):
            if isinstance(expression.callee, ast.NameExpr) and expression.callee.name == "len":
                return self._analyze_len_call(expression)
            callee_type = self._analyze_expression(expression.callee)
            argument_types = [self._analyze_expression(arg) for arg in expression.arguments]
            if not isinstance(callee_type, FunctionType):
                if not callee_type.is_error:
                    self.diagnostics.error("SEM026", "attempted to call a non-function value", expression.callee.span)
                return self._record_type(expression, ERROR)
            if len(argument_types) != len(callee_type.parameters):
                self.diagnostics.error(
                    "SEM027",
                    f"expected {len(callee_type.parameters)} arguments, got {len(argument_types)}",
                    expression.span,
                )
            for index, (expected, actual) in enumerate(zip(callee_type.parameters, argument_types), 1):
                if not is_assignable(expected, actual):
                    self.diagnostics.error(
                        "SEM028",
                        f"argument {index}: expected {expected.display()}, got {actual.display()}",
                        expression.arguments[index - 1].span,
                    )
            return self._record_type(expression, callee_type.return_type)
        if isinstance(expression, ast.IndexExpr):
            collection = self._analyze_expression(expression.collection)
            index = self._analyze_expression(expression.index)
            self._expect_type(index, INT, expression.index, "array index")
            if isinstance(collection, ArrayType):
                return self._record_type(expression, collection.element)
            if not collection.is_error:
                self.diagnostics.error("SEM029", "indexing requires an array", expression.collection.span)
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.FieldExpr):
            receiver = self._analyze_expression(expression.receiver)
            if isinstance(receiver, StructType):
                field_type = receiver.field_type(expression.name)
                if field_type is None:
                    self.diagnostics.error(
                        "SEM030",
                        f"structure {receiver.name!r} has no field {expression.name!r}",
                        expression.span,
                    )
                    return self._record_type(expression, ERROR)
                return self._record_type(expression, field_type)
            if not receiver.is_error:
                self.diagnostics.error("SEM031", "field access requires a structure value", expression.receiver.span)
            return self._record_type(expression, ERROR)
        raise AssertionError(f"unhandled expression: {type(expression).__name__}")

    def _analyze_lvalue(self, expression: ast.Expr) -> Type:
        if isinstance(expression, ast.NameExpr):
            type_ = self._analyze_expression(expression)
            symbol = self.bindings.get(id(expression))
            if not isinstance(symbol, VariableSymbol):
                self.diagnostics.error("SEM032", "assignment target is not a variable", expression.span)
            return type_
        if isinstance(expression, ast.IndexExpr):
            return self._analyze_expression(expression)
        if isinstance(expression, ast.FieldExpr):
            return self._analyze_expression(expression)
        self.diagnostics.error("SEM033", "expression is not assignable", expression.span)
        return self._analyze_expression(expression)

    def _analyze_len_call(self, expression: ast.CallExpr) -> Type:
        # Record the callee binding even though len is overloaded.
        assert isinstance(expression.callee, ast.NameExpr)
        symbol = self.scope.lookup("len")
        if symbol is not None:
            self.bindings[id(expression.callee)] = symbol
        if len(expression.arguments) != 1:
            for argument in expression.arguments:
                self._analyze_expression(argument)
            self.diagnostics.error("SEM034", "len expects exactly one argument", expression.span)
            return self._record_type(expression, ERROR)
        argument_type = self._analyze_expression(expression.arguments[0])
        if not isinstance(argument_type, ArrayType) and argument_type != STRING and not argument_type.is_error:
            self.diagnostics.error("SEM035", "len accepts an array or string", expression.arguments[0].span)
        return self._record_type(expression, INT)

    def _require_bool(self, expression: ast.Expr, context: str) -> None:
        type_ = self._analyze_expression(expression)
        self._expect_type(type_, BOOL, expression, context)

    def _expect_type(self, actual: Type, expected: Type, node: ast.Node, context: str) -> None:
        if not same_type(actual, expected):
            self.diagnostics.error(
                "SEM036",
                f"{context} requires {expected.display()}, got {actual.display()}",
                node.span,
            )

    def _record_type(self, node: ast.Node, type_: Type) -> Type:
        self.node_types[id(node)] = type_
        return type_

    def _resolve_type_syntax(self, syntax: ast.TypeSyntax | None, resolving_struct: str | None = None) -> Type:
        if syntax is None:
            return ERROR
        if syntax.element is not None:
            element = self._resolve_type_syntax(syntax.element, resolving_struct=resolving_struct)
            if element == VOID:
                self.diagnostics.error("SEM037", "array element cannot have type void", syntax.span)
                return ERROR
            return ArrayType(element, syntax.length or 0)
        builtin = {"int": INT, "bool": BOOL, "string": STRING, "void": VOID, "<error>": ERROR}
        if syntax.name in builtin:
            return builtin[syntax.name]
        if syntax.name in self.struct_declarations:
            if syntax.name == resolving_struct and self.struct_states.get(syntax.name) == "resolving":
                declaration = self.struct_declarations[syntax.name]
                self.diagnostics.error(
                    "SEM038",
                    f"structure {syntax.name!r} cannot contain itself by value",
                    declaration.span,
                )
                return ERROR
            return self._resolve_struct(syntax.name)
        self.diagnostics.error("SEM039", f"unknown type {syntax.name!r}", syntax.span)
        return ERROR

    def _always_returns(self, statement: ast.Stmt) -> bool:
        if isinstance(statement, ast.ReturnStmt):
            return True
        if isinstance(statement, ast.BlockStmt):
            for child in statement.statements:
                if self._always_returns(child):
                    return True
            return False
        if isinstance(statement, ast.IfStmt):
            if statement.else_branch is None:
                return False
            return self._always_returns(statement.then_branch) and self._always_returns(statement.else_branch)
        return False
`````

## `code/minilang/minilang/symbols.py`

`````python
"""Symbols and lexical scopes used by MiniLang semantic analysis."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import ast
from .typesys import FunctionType, StructType, Type


class SymbolKind(str, Enum):
    VARIABLE = "variable"
    PARAMETER = "parameter"
    FUNCTION = "function"
    STRUCT = "struct"
    BUILTIN = "builtin"


@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    kind: SymbolKind


@dataclass(frozen=True, slots=True)
class VariableSymbol(Symbol):
    type: Type
    mutable: bool
    depth: int


@dataclass(frozen=True, slots=True)
class FunctionSymbol(Symbol):
    type: FunctionType
    declaration: ast.FunctionDecl | None


@dataclass(frozen=True, slots=True)
class StructSymbol(Symbol):
    type: StructType
    declaration: ast.StructDecl


@dataclass(frozen=True, slots=True)
class BuiltinSymbol(Symbol):
    type: FunctionType | None


class Scope:
    def __init__(self, parent: "Scope | None" = None) -> None:
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}
        self.depth = 0 if parent is None else parent.depth + 1

    def define(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup_local(self, name: str) -> Symbol | None:
        return self.symbols.get(name)

    def lookup(self, name: str) -> Symbol | None:
        scope: Scope | None = self
        while scope is not None:
            symbol = scope.lookup_local(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None
`````

## `code/minilang/minilang/token.py`

`````python
"""Token definitions for MiniLang.

The lexer keeps source offsets and line/column information on every token so
later stages can produce precise diagnostics without rescanning the source.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    EOF = auto()
    ERROR = auto()

    IDENTIFIER = auto()
    INTEGER = auto()
    STRING = auto()

    # Keywords
    LET = auto()
    FN = auto()
    STRUCT = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    INT = auto()
    BOOL = auto()
    STRING_TYPE = auto()
    VOID = auto()

    # Punctuation
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    SEMICOLON = auto()
    ARROW = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    BANG = auto()
    EQUAL = auto()
    LESS = auto()
    GREATER = auto()
    BANG_EQUAL = auto()
    EQUAL_EQUAL = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()
    AND_AND = auto()
    OR_OR = auto()


KEYWORDS: dict[str, TokenKind] = {
    "let": TokenKind.LET,
    "fn": TokenKind.FN,
    "struct": TokenKind.STRUCT,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "for": TokenKind.FOR,
    "return": TokenKind.RETURN,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "int": TokenKind.INT,
    "bool": TokenKind.BOOL,
    "string": TokenKind.STRING_TYPE,
    "void": TokenKind.VOID,
}


@dataclass(frozen=True, slots=True)
class SourcePosition:
    offset: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start: SourcePosition
    end: SourcePosition

    @classmethod
    def covering(cls, first: "SourceSpan", second: "SourceSpan") -> "SourceSpan":
        return cls(first.start, second.end)


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    lexeme: str
    literal: object | None
    span: SourceSpan

    def __str__(self) -> str:
        literal = "" if self.literal is None else f" {self.literal!r}"
        return f"{self.kind.name} {self.lexeme!r}{literal} @{self.span.start.line}:{self.span.start.column}"
`````

## `code/minilang/minilang/typesys.py`

`````python
"""MiniLang's static type representation and compatibility rules."""
from __future__ import annotations

from dataclasses import dataclass


class Type:
    def display(self) -> str:
        raise NotImplementedError

    @property
    def is_error(self) -> bool:
        return False

    @property
    def is_scalar(self) -> bool:
        return isinstance(self, PrimitiveType) and self.name in {"int", "bool", "string"}


@dataclass(frozen=True, slots=True)
class PrimitiveType(Type):
    name: str

    def display(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class ArrayType(Type):
    element: Type
    length: int

    def display(self) -> str:
        return f"[{self.element.display()}; {self.length}]"


@dataclass(frozen=True, slots=True)
class StructType(Type):
    name: str
    fields: tuple[tuple[str, Type], ...]

    def display(self) -> str:
        return self.name

    def field_type(self, field_name: str) -> Type | None:
        for name, type_ in self.fields:
            if name == field_name:
                return type_
        return None

    def field_index(self, field_name: str) -> int | None:
        for index, (name, _) in enumerate(self.fields):
            if name == field_name:
                return index
        return None


@dataclass(frozen=True, slots=True)
class FunctionType(Type):
    parameters: tuple[Type, ...]
    return_type: Type

    def display(self) -> str:
        params = ", ".join(param.display() for param in self.parameters)
        return f"fn({params}) -> {self.return_type.display()}"


class ErrorType(Type):
    @property
    def is_error(self) -> bool:
        return True

    def display(self) -> str:
        return "<error>"

    def __repr__(self) -> str:
        return "ERROR"


INT = PrimitiveType("int")
BOOL = PrimitiveType("bool")
STRING = PrimitiveType("string")
VOID = PrimitiveType("void")
ERROR = ErrorType()


def same_type(left: Type, right: Type) -> bool:
    if left.is_error or right.is_error:
        return True
    return left == right


def is_assignable(target: Type, value: Type) -> bool:
    return same_type(target, value)
`````
