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
