"""Runnable LLVM API example using llvmlite's Python bindings."""
from __future__ import annotations

from llvmlite import binding, ir


def build_module() -> ir.Module:
    module = ir.Module(name="api_demo")
    function_type = ir.FunctionType(ir.IntType(32), ())
    function = ir.Function(module, function_type, name="main")
    entry = function.append_basic_block("entry")
    builder = ir.IRBuilder(entry)
    answer = builder.add(ir.Constant(ir.IntType(32), 40), ir.Constant(ir.IntType(32), 2), name="answer")
    builder.ret(answer)
    return module


def jit_run(module: ir.Module) -> int:
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()
    llvm_module = binding.parse_assembly(str(module))
    llvm_module.verify()
    target = binding.Target.from_default_triple()
    machine = target.create_target_machine()
    engine = binding.create_mcjit_compiler(llvm_module, machine)
    engine.finalize_object()
    address = engine.get_function_address("main")
    import ctypes

    function = ctypes.CFUNCTYPE(ctypes.c_int)(address)
    return int(function())


if __name__ == "__main__":
    module = build_module()
    print(module)
    result = jit_run(module)
    print(f"result={result}")
    raise SystemExit(0 if result == 42 else 1)
