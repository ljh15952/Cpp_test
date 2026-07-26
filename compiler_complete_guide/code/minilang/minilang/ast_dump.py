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
