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
