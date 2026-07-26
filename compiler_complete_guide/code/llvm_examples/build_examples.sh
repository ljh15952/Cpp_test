#!/bin/sh
set -eu
CLANG=${CLANG:-clang}
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT="$ROOT/generated"
mkdir -p "$OUT"

"$CLANG" -S -emit-llvm -O0 "$ROOT/pipeline.c" -o "$OUT/pipeline_O0.ll"
"$CLANG" -S -emit-llvm -O2 "$ROOT/pipeline.c" -o "$OUT/pipeline_O2.ll"
"$CLANG" -S -O2 "$ROOT/pipeline.c" -o "$OUT/x86_64.s"
"$CLANG" -target i386-unknown-linux-gnu -S -O2 -ffreestanding "$ROOT/pipeline.c" -o "$OUT/x86.s"
"$CLANG" -target aarch64-unknown-linux-gnu -S -O2 -ffreestanding "$ROOT/pipeline.c" -o "$OUT/aarch64.s"
"$CLANG" -target riscv64-unknown-linux-gnu -S -O2 -ffreestanding "$ROOT/pipeline.c" -o "$OUT/riscv64.s"
"$CLANG" "$ROOT/main.ll" -o "$OUT/main"
set +e
"$OUT/main"
STATUS=$?
set -e
[ "$STATUS" -eq 42 ]
printf 'generated LLVM IR and assembly for x86, x86-64, AArch64, and RISC-V\n'
