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
