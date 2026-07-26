"""Cytron-style phi placement and dominator-tree SSA renaming."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from dataflow import analyze_liveness
from dominators import DominatorInfo, compute_dominators
from ir import Assign, BasicBlock, Binary, Branch, Function, Instruction, Operand, Phi, Return


@dataclass(frozen=True, slots=True)
class SSAResult:
    function: Function
    dominators: DominatorInfo
    parameter_versions: dict[str, str]


def to_ssa(input_function: Function) -> SSAResult:
    function = deepcopy(input_function)
    dominators = compute_dominators(function)
    _insert_phi_functions(function, dominators)
    parameter_versions = _rename(function, dominators)
    function.validate()
    return SSAResult(function, dominators, parameter_versions)


def _insert_phi_functions(function: Function, dominators: DominatorInfo) -> None:
    # Pruned SSA places a phi only when the variable is live-in at the
    # dominance-frontier block. This avoids meaningless phis such as a loop
    # condition temporary that is redefined before every use.
    liveness = analyze_liveness(function)
    definitions: dict[str, set[str]] = {variable: set() for variable in function.variables()}
    for block_name, block in function.blocks.items():
        for instruction in block.instructions:
            definition = instruction.definition()
            if definition is not None:
                definitions.setdefault(definition, set()).add(block_name)

    for variable, sites in sorted(definitions.items()):
        worklist = list(sites)
        has_phi: set[str] = set()
        while worklist:
            block_name = worklist.pop()
            for frontier_block in dominators.frontier[block_name]:
                if frontier_block in has_phi or variable not in liveness.live_in[frontier_block]:
                    continue
                block = function.blocks[frontier_block]
                insertion = 0
                while insertion < len(block.instructions) and isinstance(block.instructions[insertion], Phi):
                    insertion += 1
                block.instructions.insert(insertion, Phi(variable))
                has_phi.add(frontier_block)
                if frontier_block not in sites:
                    worklist.append(frontier_block)


def _rename(function: Function, dominators: DominatorInfo) -> dict[str, str]:
    counters: dict[str, int] = {}
    stacks: dict[str, list[str]] = {}

    def fresh(variable: str) -> str:
        number = counters.get(variable, 0)
        counters[variable] = number + 1
        return f"{variable}.{number}"

    def push(variable: str) -> str:
        version = fresh(variable)
        stacks.setdefault(variable, []).append(version)
        return version

    def top(variable: str) -> str:
        stack = stacks.get(variable)
        if not stack:
            raise ValueError(f"variable {variable!r} is used before definition")
        return stack[-1]

    parameter_versions: dict[str, str] = {}
    for parameter in function.parameters:
        parameter_versions[parameter] = push(parameter)
    function.parameters[:] = [parameter_versions[name] for name in function.parameters]

    def rename_operand(operand: Operand) -> Operand:
        if operand.name is None:
            return operand
        return Operand.var(top(operand.name))

    def rename_block(block_name: str) -> None:
        block = function.blocks[block_name]
        pushed: list[str] = []

        # Phi definitions conceptually occur at the beginning of the block.
        for instruction in block.instructions:
            if not isinstance(instruction, Phi):
                break
            instruction.target = push(instruction.variable)
            pushed.append(instruction.variable)

        for instruction in block.instructions:
            if isinstance(instruction, Phi):
                continue
            if isinstance(instruction, Assign):
                instruction.value = rename_operand(instruction.value)
                original = instruction.target
                instruction.target = push(original)
                pushed.append(original)
            elif isinstance(instruction, Binary):
                instruction.left = rename_operand(instruction.left)
                instruction.right = rename_operand(instruction.right)
                original = instruction.target
                instruction.target = push(original)
                pushed.append(original)
            elif isinstance(instruction, Branch):
                instruction.condition = rename_operand(instruction.condition)
            elif isinstance(instruction, Return):
                instruction.value = rename_operand(instruction.value)

        for successor_name in block.successors():
            successor = function.blocks[successor_name]
            for instruction in successor.instructions:
                if not isinstance(instruction, Phi):
                    break
                instruction.incoming[block_name] = Operand.var(top(instruction.variable))

        for child in dominators.tree_children[block_name]:
            rename_block(child)

        for variable in reversed(pushed):
            stacks[variable].pop()

    rename_block(function.entry)
    return parameter_versions
