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
