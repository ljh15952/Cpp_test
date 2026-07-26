# Optimization laboratory

This standalone laboratory implements:

- iterative dominator computation;
- immediate dominators and dominance frontiers;
- Cytron-style phi placement;
- dominator-tree SSA renaming;
- backward liveness analysis with edge-sensitive phi uses;
- live intervals and linear-scan register allocation.

```bash
python -m unittest -v
python demo.py
```
