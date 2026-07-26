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
