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
