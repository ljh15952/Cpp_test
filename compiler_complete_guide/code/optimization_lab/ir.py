"""Small three-address IR used for SSA, liveness, and register-allocation labs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Operand:
    name: str | None = None
    constant: int | None = None

    @classmethod
    def var(cls, name: str) -> "Operand":
        return cls(name=name)

    @classmethod
    def const(cls, value: int) -> "Operand":
        return cls(constant=value)

    @property
    def is_variable(self) -> bool:
        return self.name is not None

    def __str__(self) -> str:
        return self.name if self.name is not None else str(self.constant)


class Instruction:
    def uses(self) -> tuple[str, ...]:
        return ()

    def definition(self) -> str | None:
        return None


@dataclass(slots=True)
class Assign(Instruction):
    target: str
    value: Operand

    def uses(self) -> tuple[str, ...]:
        return (self.value.name,) if self.value.name is not None else ()

    def definition(self) -> str:
        return self.target

    def __str__(self) -> str:
        return f"{self.target} = {self.value}"


@dataclass(slots=True)
class Binary(Instruction):
    target: str
    operator: str
    left: Operand
    right: Operand

    def uses(self) -> tuple[str, ...]:
        return tuple(value.name for value in (self.left, self.right) if value.name is not None)

    def definition(self) -> str:
        return self.target

    def __str__(self) -> str:
        return f"{self.target} = {self.left} {self.operator} {self.right}"


@dataclass(slots=True)
class Phi(Instruction):
    variable: str
    target: str | None = None
    incoming: dict[str, Operand] = field(default_factory=dict)

    def uses(self) -> tuple[str, ...]:
        return tuple(value.name for value in self.incoming.values() if value.name is not None)

    def definition(self) -> str:
        return self.target or self.variable

    def __str__(self) -> str:
        target = self.target or self.variable
        incoming = ", ".join(f"[{value}, %{block}]" for block, value in sorted(self.incoming.items()))
        return f"{target} = phi {incoming}"


@dataclass(slots=True)
class Jump(Instruction):
    target: str

    def __str__(self) -> str:
        return f"jump %{self.target}"


@dataclass(slots=True)
class Branch(Instruction):
    condition: Operand
    true_target: str
    false_target: str

    def uses(self) -> tuple[str, ...]:
        return (self.condition.name,) if self.condition.name is not None else ()

    def __str__(self) -> str:
        return f"branch {self.condition}, %{self.true_target}, %{self.false_target}"


@dataclass(slots=True)
class Return(Instruction):
    value: Operand

    def uses(self) -> tuple[str, ...]:
        return (self.value.name,) if self.value.name is not None else ()

    def __str__(self) -> str:
        return f"return {self.value}"


Terminator = Jump | Branch | Return


@dataclass(slots=True)
class BasicBlock:
    name: str
    instructions: list[Instruction] = field(default_factory=list)

    def append(self, instruction: Instruction) -> None:
        if self.instructions and isinstance(self.instructions[-1], (Jump, Branch, Return)):
            raise ValueError(f"block {self.name!r} already has a terminator")
        self.instructions.append(instruction)

    @property
    def terminator(self) -> Terminator:
        if not self.instructions or not isinstance(self.instructions[-1], (Jump, Branch, Return)):
            raise ValueError(f"block {self.name!r} has no terminator")
        return self.instructions[-1]

    def successors(self) -> tuple[str, ...]:
        terminator = self.terminator
        if isinstance(terminator, Jump):
            return (terminator.target,)
        if isinstance(terminator, Branch):
            return (terminator.true_target, terminator.false_target)
        return ()

    def __str__(self) -> str:
        body = "\n".join(f"  {instruction}" for instruction in self.instructions)
        return f"{self.name}:\n{body}"


@dataclass(slots=True)
class Function:
    name: str
    entry: str
    parameters: list[str]
    blocks: dict[str, BasicBlock]

    def validate(self) -> None:
        if self.entry not in self.blocks:
            raise ValueError(f"entry block {self.entry!r} is missing")
        for name, block in self.blocks.items():
            if name != block.name:
                raise ValueError(f"block key {name!r} does not match {block.name!r}")
            for successor in block.successors():
                if successor not in self.blocks:
                    raise ValueError(f"block {name!r} jumps to missing block {successor!r}")
        reachable = set(self.reverse_postorder())
        unreachable = set(self.blocks) - reachable
        if unreachable:
            raise ValueError(f"unreachable blocks: {sorted(unreachable)}")

    def predecessors(self) -> dict[str, set[str]]:
        result = {name: set() for name in self.blocks}
        for name, block in self.blocks.items():
            for successor in block.successors():
                result[successor].add(name)
        return result

    def reverse_postorder(self) -> list[str]:
        visited: set[str] = set()
        postorder: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            for successor in self.blocks[name].successors():
                visit(successor)
            postorder.append(name)

        visit(self.entry)
        postorder.reverse()
        return postorder

    def variables(self) -> set[str]:
        result = set(self.parameters)
        for block in self.blocks.values():
            for instruction in block.instructions:
                definition = instruction.definition()
                if definition is not None:
                    result.add(definition)
                result.update(instruction.uses())
        return result

    def __str__(self) -> str:
        parameters = ", ".join(self.parameters)
        blocks = "\n".join(str(self.blocks[name]) for name in self.reverse_postorder())
        return f"function {self.name}({parameters})\n{blocks}"


def op(value: str | int) -> Operand:
    return Operand.var(value) if isinstance(value, str) else Operand.const(value)


def block(name: str, *instructions: Instruction) -> BasicBlock:
    return BasicBlock(name, list(instructions))
