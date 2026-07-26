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
