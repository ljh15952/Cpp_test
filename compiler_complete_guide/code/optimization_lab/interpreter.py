"""Interpreter for both conventional and SSA forms of the teaching IR."""
from __future__ import annotations

from ir import Assign, Binary, Branch, Function, Jump, Operand, Phi, Return


def execute(function: Function, arguments: list[int]) -> int:
    function.validate()
    if len(arguments) != len(function.parameters):
        raise ValueError("argument count mismatch")
    values = dict(zip(function.parameters, arguments))
    current = function.entry
    predecessor: str | None = None

    def read(operand: Operand) -> int:
        if operand.name is None:
            assert operand.constant is not None
            return operand.constant
        if operand.name not in values:
            raise ValueError(f"read of undefined variable {operand.name!r}")
        return values[operand.name]

    while True:
        block = function.blocks[current]
        index = 0
        while index < len(block.instructions) and isinstance(block.instructions[index], Phi):
            phi = block.instructions[index]
            if predecessor is None or predecessor not in phi.incoming:
                raise ValueError(f"phi in {current!r} has no input from {predecessor!r}")
            target = phi.definition()
            values[target] = read(phi.incoming[predecessor])
            index += 1

        while index < len(block.instructions):
            instruction = block.instructions[index]
            if isinstance(instruction, Assign):
                values[instruction.target] = read(instruction.value)
            elif isinstance(instruction, Binary):
                left = read(instruction.left)
                right = read(instruction.right)
                operations = {
                    "+": lambda: left + right,
                    "-": lambda: left - right,
                    "*": lambda: left * right,
                    "<": lambda: int(left < right),
                    "<=": lambda: int(left <= right),
                    ">": lambda: int(left > right),
                    ">=": lambda: int(left >= right),
                    "==": lambda: int(left == right),
                }
                try:
                    values[instruction.target] = operations[instruction.operator]()
                except KeyError as exc:
                    raise ValueError(f"unknown operator {instruction.operator!r}") from exc
            elif isinstance(instruction, Jump):
                predecessor, current = current, instruction.target
                break
            elif isinstance(instruction, Branch):
                predecessor = current
                current = instruction.true_target if read(instruction.condition) else instruction.false_target
                break
            elif isinstance(instruction, Return):
                return read(instruction.value)
            elif isinstance(instruction, Phi):
                raise ValueError("phi must appear at block start")
            index += 1
        else:
            raise ValueError(f"block {current!r} has no terminator")
