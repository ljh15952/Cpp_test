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
