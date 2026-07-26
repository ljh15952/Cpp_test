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
