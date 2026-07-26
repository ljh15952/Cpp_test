"""Backward liveness analysis over the teaching IR."""
from __future__ import annotations

from dataclasses import dataclass

from ir import Function, Phi


@dataclass(frozen=True, slots=True)
class Liveness:
    live_in: dict[str, frozenset[str]]
    live_out: dict[str, frozenset[str]]
    use: dict[str, frozenset[str]]
    definitions: dict[str, frozenset[str]]


def analyze_liveness(function: Function) -> Liveness:
    function.validate()
    use: dict[str, set[str]] = {name: set() for name in function.blocks}
    definitions: dict[str, set[str]] = {name: set() for name in function.blocks}

    # Phi operands are uses on incoming CFG edges, not ordinary uses in the phi block.
    edge_phi_uses: dict[tuple[str, str], set[str]] = {}
    for successor_name, successor in function.blocks.items():
        for instruction in successor.instructions:
            if not isinstance(instruction, Phi):
                break
            for predecessor, operand in instruction.incoming.items():
                if operand.name is not None:
                    edge_phi_uses.setdefault((predecessor, successor_name), set()).add(operand.name)
            definition = instruction.definition()
            if definition is not None:
                definitions[successor_name].add(definition)

    for block_name, block in function.blocks.items():
        for instruction in block.instructions:
            if isinstance(instruction, Phi):
                continue
            for variable in instruction.uses():
                if variable not in definitions[block_name]:
                    use[block_name].add(variable)
            definition = instruction.definition()
            if definition is not None:
                definitions[block_name].add(definition)

    live_in = {name: set() for name in function.blocks}
    live_out = {name: set() for name in function.blocks}
    changed = True
    while changed:
        changed = False
        for block_name in reversed(function.reverse_postorder()):
            block = function.blocks[block_name]
            new_out: set[str] = set()
            for successor in block.successors():
                successor_in = live_in[successor] - {
                    instruction.definition()
                    for instruction in function.blocks[successor].instructions
                    if isinstance(instruction, Phi)
                }
                new_out.update(successor_in)
                new_out.update(edge_phi_uses.get((block_name, successor), set()))
            new_in = use[block_name] | (new_out - definitions[block_name])
            if new_out != live_out[block_name] or new_in != live_in[block_name]:
                live_out[block_name] = new_out
                live_in[block_name] = new_in
                changed = True

    return Liveness(
        {name: frozenset(values) for name, values in live_in.items()},
        {name: frozenset(values) for name, values in live_out.items()},
        {name: frozenset(values) for name, values in use.items()},
        {name: frozenset(values) for name, values in definitions.items()},
    )
