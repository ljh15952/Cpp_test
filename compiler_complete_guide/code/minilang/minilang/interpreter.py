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
