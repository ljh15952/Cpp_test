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
