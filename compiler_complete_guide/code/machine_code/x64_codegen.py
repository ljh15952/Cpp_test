#!/usr/bin/env python3
"""Direct x86-64 machine-code generator for integer expressions.

This deliberately bypasses an assembler. It emits instruction bytes for the
System V AMD64 ABI, executes them from an mmap page, and can wrap the same code
in a minimal ELF64 executable.
"""
from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import mmap
from pathlib import Path
import platform
import struct
import subprocess
import sys
from typing import Iterator


class CodegenError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    text: str
    value: int | None = None


def tokenize(source: str) -> Iterator[Token]:
    index = 0
    while index < len(source):
        ch = source[index]
        if ch.isspace():
            index += 1
            continue
        if ch.isdigit():
            start = index
            index += 1
            while index < len(source) and (source[index].isalnum() or source[index] == "_"):
                index += 1
            text = source[start:index]
            try:
                value = int(text.replace("_", ""), 0)
            except ValueError as exc:
                raise CodegenError(f"invalid integer literal {text!r}") from exc
            yield Token("integer", text, value)
            continue
        if ch in "+-*/%()":
            yield Token(ch, ch)
            index += 1
            continue
        raise CodegenError(f"unexpected character {ch!r} at offset {index}")
    yield Token("eof", "")


class Expr:
    pass


@dataclass(frozen=True, slots=True)
class IntegerExpr(Expr):
    value: int


@dataclass(frozen=True, slots=True)
class UnaryExpr(Expr):
    operator: str
    operand: Expr


@dataclass(frozen=True, slots=True)
class BinaryExpr(Expr):
    left: Expr
    operator: str
    right: Expr


class Parser:
    def __init__(self, source: str) -> None:
        self.tokens = list(tokenize(source))
        self.index = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.index]

    def parse(self) -> Expr:
        expression = self._expression(0)
        if self.current.kind != "eof":
            raise CodegenError(f"unexpected token {self.current.text!r}")
        return expression

    def _expression(self, minimum_precedence: int) -> Expr:
        left = self._prefix()
        precedence = {"+": 10, "-": 10, "*": 20, "/": 20, "%": 20}
        while precedence.get(self.current.kind, -1) > minimum_precedence:
            operator = self._advance().kind
            right = self._expression(precedence[operator])
            left = BinaryExpr(left, operator, right)
        return left

    def _prefix(self) -> Expr:
        token = self._advance()
        if token.kind == "integer":
            assert token.value is not None
            return IntegerExpr(token.value)
        if token.kind in {"+", "-"}:
            return UnaryExpr(token.kind, self._expression(30))
        if token.kind == "(":
            expression = self._expression(0)
            self._expect(")")
            return expression
        raise CodegenError(f"expected expression, found {token.text!r}")

    def _expect(self, kind: str) -> None:
        if self.current.kind != kind:
            raise CodegenError(f"expected {kind!r}, found {self.current.text!r}")
        self._advance()

    def _advance(self) -> Token:
        token = self.current
        if token.kind != "eof":
            self.index += 1
        return token


class X64Emitter:
    """Encode a small x86-64 instruction subset without an assembler."""

    def __init__(self) -> None:
        self.code = bytearray()

    def emit_function(self, expression: Expr) -> bytes:
        self.code.clear()
        self._expression(expression)
        self._bytes(0xC3)  # ret
        return bytes(self.code)

    def emit_process_entry(self, expression: Expr) -> bytes:
        """Emit Linux _start: evaluate, then exit(result & 255)."""
        self.code.clear()
        self._expression(expression)
        # mov rdi, rax
        self._bytes(0x48, 0x89, 0xC7)
        # mov rax, 60 (SYS_exit)
        self._bytes(0x48, 0xC7, 0xC0)
        self.code.extend(struct.pack("<I", 60))
        # syscall
        self._bytes(0x0F, 0x05)
        return bytes(self.code)

    def _expression(self, expression: Expr) -> None:
        if isinstance(expression, IntegerExpr):
            self._mov_rax_imm64(expression.value)
            return
        if isinstance(expression, UnaryExpr):
            self._expression(expression.operand)
            if expression.operator == "-":
                self._bytes(0x48, 0xF7, 0xD8)  # neg rax
            elif expression.operator != "+":
                raise CodegenError(f"unsupported unary operator {expression.operator}")
            return
        if isinstance(expression, BinaryExpr):
            self._expression(expression.left)
            self._bytes(0x50)  # push rax
            self._expression(expression.right)
            self._bytes(0x59)  # pop rcx; rcx=left, rax=right
            if expression.operator == "+":
                self._bytes(0x48, 0x01, 0xC8)  # add rax, rcx
            elif expression.operator == "-":
                self._bytes(0x48, 0x29, 0xC1)  # sub rcx, rax
                self._bytes(0x48, 0x89, 0xC8)  # mov rax, rcx
            elif expression.operator == "*":
                self._bytes(0x48, 0x0F, 0xAF, 0xC1)  # imul rax, rcx
            elif expression.operator in {"/", "%"}:
                # rsi=right, rax=left, rdx:rax sign extension, idiv rsi
                self._bytes(0x48, 0x89, 0xC6)  # mov rsi, rax
                self._bytes(0x48, 0x89, 0xC8)  # mov rax, rcx
                self._bytes(0x48, 0x99)        # cqo
                self._bytes(0x48, 0xF7, 0xFE)  # idiv rsi
                if expression.operator == "%":
                    self._bytes(0x48, 0x89, 0xD0)  # mov rax, rdx
            else:
                raise CodegenError(f"unsupported binary operator {expression.operator}")
            return
        raise CodegenError(f"unsupported AST node {type(expression).__name__}")

    def _mov_rax_imm64(self, value: int) -> None:
        if not -(1 << 63) <= value < (1 << 63):
            raise CodegenError(f"integer {value} is outside signed 64-bit range")
        self._bytes(0x48, 0xB8)
        self.code.extend(struct.pack("<q", value))

    def _bytes(self, *values: int) -> None:
        self.code.extend(values)


def execute(code: bytes) -> int:
    if platform.machine().lower() not in {"x86_64", "amd64"}:
        raise CodegenError("native execution requires an x86-64 host")
    page = mmap.mmap(
        -1,
        len(code),
        flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS,
        prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC,
    )
    try:
        page.write(code)
        address = ctypes.addressof(ctypes.c_char.from_buffer(page))
        function = ctypes.CFUNCTYPE(ctypes.c_int64)(address)
        return int(function())
    finally:
        page.close()


def write_elf64(path: Path, code: bytes) -> None:
    """Write a minimal static ELF64 image containing one RX load segment."""
    if platform.system() != "Linux":
        raise CodegenError("ELF emission is supported on Linux")

    base_address = 0x400000
    code_offset = 0x1000
    entry_address = base_address + code_offset

    elf_ident = bytearray(16)
    elf_ident[0:4] = b"\x7fELF"
    elf_ident[4] = 2  # ELFCLASS64
    elf_ident[5] = 1  # ELFDATA2LSB
    elf_ident[6] = 1  # EV_CURRENT
    elf_ident[7] = 0  # System V ABI

    elf_header = struct.pack(
        "<16sHHIQQQIHHHHHH",
        bytes(elf_ident),
        2,             # ET_EXEC
        62,            # EM_X86_64
        1,             # EV_CURRENT
        entry_address,
        64,            # program header offset
        0,             # section header offset
        0,             # flags
        64,            # ELF header size
        56,            # program header entry size
        1,             # program header count
        0, 0, 0,       # no section headers
    )
    file_size = code_offset + len(code)
    program_header = struct.pack(
        "<IIQQQQQQ",
        1,             # PT_LOAD
        5,             # PF_R | PF_X
        0,             # file offset
        base_address,
        base_address,
        file_size,
        file_size,
        0x1000,
    )
    image = bytearray(elf_header + program_header)
    image.extend(b"\x00" * (code_offset - len(image)))
    image.extend(code)
    path.write_bytes(image)
    path.chmod(0o755)


def disassemble(code_path: Path) -> str | None:
    """Use objdump when available; code generation itself does not depend on it."""
    from shutil import which

    objdump = which("objdump")
    if objdump is None:
        return None
    completed = subprocess.run(
        [objdump, "-D", "-b", "binary", "-m", "i386:x86-64", str(code_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expression", help="integer expression, for example '(2 + 3) * 4'")
    parser.add_argument("--raw", type=Path, help="write raw function bytes")
    parser.add_argument("--elf", type=Path, help="write a Linux ELF64 executable")
    parser.add_argument("--no-execute", action="store_true", help="do not execute generated function")
    args = parser.parse_args(argv)

    try:
        tree = Parser(args.expression).parse()
        emitter = X64Emitter()
        function_code = emitter.emit_function(tree)
        print("machine code:", function_code.hex(" "))
        if args.raw is not None:
            args.raw.write_bytes(function_code)
            listing = disassemble(args.raw)
            if listing:
                print(listing.rstrip())
        if args.elf is not None:
            process_code = emitter.emit_process_entry(tree)
            write_elf64(args.elf, process_code)
            print(f"ELF64: {args.elf}")
        if not args.no_execute:
            print("result:", execute(function_code))
        return 0
    except (CodegenError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
