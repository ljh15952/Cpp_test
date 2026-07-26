# LLVM and multi-ISA examples

```bash
./build_examples.sh
```

Generated files include unoptimized and optimized LLVM IR plus assembly for
32-bit x86, x86-64, AArch64, and RV64. Cross-assembly uses freestanding C, so a
foreign sysroot is unnecessary.
