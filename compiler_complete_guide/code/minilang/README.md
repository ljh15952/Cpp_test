# MiniLang reference compiler

This directory contains the executable compiler used throughout the book.

```bash
export PYTHONPATH=$PWD
python -m minilang check examples/arrays_structs.mini
python -m minilang run examples/fibonacci.mini
python -m minilang emit-llvm examples/control_flow.mini -o control_flow.ll
python -m minilang build examples/control_flow.mini -o control_flow
./control_flow
python -m unittest discover -s tests -v
```

MiniLang 1.0 supports `int`, `bool`, UTF-8 strings, fixed-size arrays,
structures, functions, lexical scope, `if`, `while`, C-style `for`, assignment,
and `return`. Aggregate parameters are passed with value semantics. To keep the
teaching ABI compact, function return types are scalar or `void`.
