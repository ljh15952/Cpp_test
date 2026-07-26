# 부록 D. 최적화 연구실 전체 소스

CFG, 지배, SSA, 활성 분석, linear-scan 할당과 테스트.
수록 파일 8개, 약 768줄.


이 부록의 코드는 본문에서 사용한 검증 원본이다. 줄 번호는 편집·수정에 따라 바뀔 수 있으므로 클래스·함수 이름으로 찾아간다.

## `code/optimization_lab/dataflow.py`

`````python
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
`````

## `code/optimization_lab/demo.py`

`````python
from __future__ import annotations

from dataflow import analyze_liveness
from dominators import compute_dominators
from interpreter import execute
from ir import Assign, Binary, Branch, Function, Jump, Return, block, op
from regalloc import linear_scan
from ssa import to_ssa


def sample() -> Function:
    # Computes the sum 1 + ... + n using a loop.
    return Function(
        "sum_to",
        "entry",
        ["n"],
        {
            "entry": block("entry", Assign("i", op(1)), Assign("sum", op(0)), Jump("header")),
            "header": block("header", Binary("cond", "<=", op("i"), op("n")), Branch(op("cond"), "body", "exit")),
            "body": block("body", Binary("sum", "+", op("sum"), op("i")), Binary("i", "+", op("i"), op(1)), Jump("header")),
            "exit": block("exit", Return(op("sum"))),
        },
    )


def main() -> None:
    conventional = sample()
    print("== Conventional IR ==")
    print(conventional)
    print("result(10) =", execute(conventional, [10]))

    dominators = compute_dominators(conventional)
    print("\n== Dominance frontier ==")
    for name in conventional.reverse_postorder():
        print(f"{name}: {sorted(dominators.frontier[name])}")

    result = to_ssa(conventional)
    print("\n== SSA IR ==")
    print(result.function)
    print("result(10) =", execute(result.function, [10]))

    liveness = analyze_liveness(result.function)
    print("\n== Live sets ==")
    for name in result.function.reverse_postorder():
        print(f"{name}: in={sorted(liveness.live_in[name])}, out={sorted(liveness.live_out[name])}")

    allocation = linear_scan(result.function, ("rax", "rcx", "rdx"))
    print("\n== Linear-scan allocation ==")
    for interval in allocation.intervals:
        print(f"{interval.variable:8} [{interval.start:2}, {interval.end:2}] -> {allocation.locations[interval.variable]}")
    print("spill slots:", allocation.spill_slots)


if __name__ == "__main__":
    main()
`````

## `code/optimization_lab/dominators.py`

`````python
"""Dominator tree and dominance-frontier algorithms for a control-flow graph."""
from __future__ import annotations

from dataclasses import dataclass

from ir import Function


@dataclass(frozen=True, slots=True)
class DominatorInfo:
    dominators: dict[str, frozenset[str]]
    immediate_dominator: dict[str, str | None]
    tree_children: dict[str, tuple[str, ...]]
    frontier: dict[str, frozenset[str]]


def compute_dominators(function: Function) -> DominatorInfo:
    function.validate()
    names = set(function.blocks)
    predecessors = function.predecessors()
    dominators: dict[str, set[str]] = {
        name: ({name} if name == function.entry else set(names)) for name in function.blocks
    }

    changed = True
    while changed:
        changed = False
        for name in function.reverse_postorder():
            if name == function.entry:
                continue
            pred_sets = [dominators[pred] for pred in predecessors[name]]
            intersection = set.intersection(*pred_sets) if pred_sets else set()
            updated = {name} | intersection
            if updated != dominators[name]:
                dominators[name] = updated
                changed = True

    immediate: dict[str, str | None] = {function.entry: None}
    for name in function.blocks:
        if name == function.entry:
            continue
        strict = dominators[name] - {name}
        if not strict:
            raise ValueError(f"block {name!r} has no strict dominator")
        # The immediate dominator is the strict dominator with greatest depth.
        immediate[name] = max(strict, key=lambda candidate: len(dominators[candidate]))

    children: dict[str, list[str]] = {name: [] for name in function.blocks}
    for name, parent in immediate.items():
        if parent is not None:
            children[parent].append(name)
    for values in children.values():
        values.sort()

    frontier: dict[str, set[str]] = {name: set() for name in function.blocks}
    for name in function.blocks:
        if len(predecessors[name]) < 2:
            continue
        stop = immediate[name]
        for predecessor in predecessors[name]:
            runner: str | None = predecessor
            while runner is not None and runner != stop:
                frontier[runner].add(name)
                runner = immediate[runner]

    return DominatorInfo(
        {name: frozenset(values) for name, values in dominators.items()},
        immediate,
        {name: tuple(values) for name, values in children.items()},
        {name: frozenset(values) for name, values in frontier.items()},
    )
`````

## `code/optimization_lab/interpreter.py`

`````python
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
`````

## `code/optimization_lab/ir.py`

`````python
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
`````

## `code/optimization_lab/regalloc.py`

`````python
"""Live-interval construction and linear-scan register allocation."""
from __future__ import annotations

from dataclasses import dataclass

from ir import Function, Phi


@dataclass(frozen=True, slots=True, order=True)
class Interval:
    start: int
    end: int
    variable: str


@dataclass(frozen=True, slots=True)
class Allocation:
    locations: dict[str, str]
    intervals: tuple[Interval, ...]
    spill_slots: int


def build_intervals(function: Function) -> tuple[Interval, ...]:
    function.validate()
    positions: dict[tuple[str, int], int] = {}
    block_start: dict[str, int] = {}
    block_end: dict[str, int] = {}
    position = 0
    for block_name in function.reverse_postorder():
        block_start[block_name] = position
        for index, _ in enumerate(function.blocks[block_name].instructions):
            positions[(block_name, index)] = position
            position += 2
        block_end[block_name] = max(block_start[block_name], position - 1)

    ranges: dict[str, list[int]] = {}

    def touch(variable: str, point: int) -> None:
        if variable not in ranges:
            ranges[variable] = [point, point]
        else:
            ranges[variable][0] = min(ranges[variable][0], point)
            ranges[variable][1] = max(ranges[variable][1], point)

    for parameter in function.parameters:
        touch(parameter, block_start[function.entry])

    for block_name in function.reverse_postorder():
        block = function.blocks[block_name]
        for index, instruction in enumerate(block.instructions):
            point = positions[(block_name, index)]
            definition = instruction.definition()
            if definition is not None:
                touch(definition, point)
            if isinstance(instruction, Phi):
                for predecessor, operand in instruction.incoming.items():
                    if operand.name is not None:
                        touch(operand.name, block_end[predecessor])
            else:
                for variable in instruction.uses():
                    touch(variable, point)

    return tuple(sorted(Interval(start, end, variable) for variable, (start, end) in ranges.items()))


def linear_scan(function: Function, registers: tuple[str, ...] = ("r0", "r1", "r2")) -> Allocation:
    intervals = build_intervals(function)
    active: list[Interval] = []
    locations: dict[str, str] = {}
    free = list(registers)
    spill_slots = 0

    def expire(current: Interval) -> None:
        nonlocal active
        still_active: list[Interval] = []
        for interval in active:
            if interval.end < current.start:
                location = locations[interval.variable]
                if location in registers:
                    free.append(location)
            else:
                still_active.append(interval)
        active = sorted(still_active, key=lambda item: item.end)
        free.sort()

    for current in intervals:
        expire(current)
        if free:
            locations[current.variable] = free.pop(0)
            active.append(current)
            active.sort(key=lambda item: item.end)
            continue

        spill = max(active, key=lambda item: item.end)
        if spill.end > current.end:
            locations[current.variable] = locations[spill.variable]
            locations[spill.variable] = f"stack[{spill_slots}]"
            spill_slots += 1
            active.remove(spill)
            active.append(current)
            active.sort(key=lambda item: item.end)
        else:
            locations[current.variable] = f"stack[{spill_slots}]"
            spill_slots += 1

    return Allocation(locations, intervals, spill_slots)
`````

## `code/optimization_lab/ssa.py`

`````python
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
`````

## `code/optimization_lab/test_optimization_lab.py`

`````python
from __future__ import annotations

import unittest

from dataflow import analyze_liveness
from demo import sample
from dominators import compute_dominators
from interpreter import execute
from ir import Phi
from regalloc import linear_scan
from ssa import to_ssa


class OptimizationLabTests(unittest.TestCase):
    def test_dominators_and_frontier(self) -> None:
        function = sample()
        info = compute_dominators(function)
        self.assertEqual(info.immediate_dominator["header"], "entry")
        self.assertEqual(info.immediate_dominator["body"], "header")
        self.assertEqual(info.immediate_dominator["exit"], "header")
        self.assertIn("header", info.frontier["body"])
        self.assertIn("header", info.frontier["header"])

    def test_ssa_preserves_execution(self) -> None:
        conventional = sample()
        result = to_ssa(conventional)
        for value in (0, 1, 2, 10, 100):
            self.assertEqual(execute(conventional, [value]), execute(result.function, [value]))
        phis = [
            instruction
            for instruction in result.function.blocks["header"].instructions
            if isinstance(instruction, Phi)
        ]
        self.assertEqual({phi.variable for phi in phis}, {"i", "sum"})
        self.assertTrue(all(len(phi.incoming) == 2 for phi in phis))

    def test_liveness_and_register_allocation(self) -> None:
        function = to_ssa(sample()).function
        liveness = analyze_liveness(function)
        self.assertIn("n.0", liveness.live_in["header"])
        allocation = linear_scan(function, ("r0", "r1"))
        self.assertEqual(set(allocation.locations), {interval.variable for interval in allocation.intervals})
        self.assertGreaterEqual(allocation.spill_slots, 1)


if __name__ == "__main__":
    unittest.main()
`````
