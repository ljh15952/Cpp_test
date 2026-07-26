"""LLVM IR backend for the MiniLang teaching compiler.

The backend emits modern opaque-pointer LLVM IR and intentionally keeps local
variables in stack slots. Running `opt -passes=mem2reg` or compiling with
`clang -O1` demonstrates promotion to SSA form.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ast
from .semantic import AnalysisResult
from .symbols import BuiltinSymbol, FunctionSymbol, VariableSymbol
from .typesys import ArrayType, BOOL, ERROR, INT, STRING, VOID, FunctionType, StructType, Type


class CodegenError(RuntimeError):
    pass


@dataclass(slots=True)
class _Block:
    label: str
    instructions: list[str] = field(default_factory=list)
    terminated: bool = False


@dataclass(frozen=True, slots=True)
class _Value:
    type: Type
    operand: str


class LLVMBackend:
    def __init__(self, program: ast.Program, analysis: AnalysisResult, module_name: str = "minilang") -> None:
        self.program = program
        self.analysis = analysis
        self.module_name = module_name
        self.functions_text: list[str] = []
        self.string_globals: dict[str, tuple[str, int]] = {}
        self.string_order: list[str] = []
        self.register_counter = 0
        self.label_counter = 0
        self.temp_counter = 0
        self.blocks: list[_Block] = []
        self.current: _Block | None = None
        self.entry_allocas: list[str] = []
        self.storage: dict[VariableSymbol, str] = {}
        self.current_function: FunctionSymbol | None = None

    def emit(self) -> str:
        for declaration in self.program.declarations:
            if isinstance(declaration, ast.FunctionDecl):
                symbol = self.analysis.functions.get(declaration.name)
                if symbol is None or symbol.declaration is not declaration:
                    # Optimized trees are reanalyzed; this guard mainly protects
                    # malformed clients that mix a tree with another analysis.
                    symbol = self.analysis.declarations.get(id(declaration))  # type: ignore[assignment]
                if not isinstance(symbol, FunctionSymbol):
                    raise CodegenError(f"missing function symbol for {declaration.name}")
                self.functions_text.append(self._emit_function(declaration, symbol))

        lines = [
            f"; ModuleID = '{self.module_name}'",
            f'source_filename = "{self._escape_identifier(self.module_name)}"',
            "",
            "%MiniLangBoolText = type { ptr }",
        ]
        for name in sorted(self.analysis.structs):
            struct_type = self.analysis.structs[name].type
            fields = ", ".join(self._llvm_type(type_) for _, type_ in struct_type.fields)
            lines.append(f"%struct.{self._mangle(name)} = type {{ {fields} }}")
        lines.extend(
            [
                "",
                '@.fmt.int = private unnamed_addr constant [5 x i8] c"%ld\\0A\\00", align 1',
                '@.bool.true = private unnamed_addr constant [5 x i8] c"true\\00", align 1',
                '@.bool.false = private unnamed_addr constant [6 x i8] c"false\\00", align 1',
                '@.assert.msg = private unnamed_addr constant [26 x i8] c"MiniLang assertion failed\\00", align 1',
            ]
        )
        for value in self.string_order:
            global_name, length = self.string_globals[value]
            encoded = self._llvm_c_string(value)
            lines.append(
                f"{global_name} = private unnamed_addr constant [{length} x i8] c\"{encoded}\", align 1"
            )
        lines.extend(
            [
                "",
                "declare i32 @printf(ptr, ...)",
                "declare i32 @puts(ptr)",
                "declare i64 @strlen(ptr)",
                "declare i32 @strcmp(ptr, ptr)",
                "declare void @abort() noreturn nounwind",
                "",
            ]
        )
        lines.extend(self.functions_text)
        return "\n".join(lines).rstrip() + "\n"

    def _emit_function(self, declaration: ast.FunctionDecl, symbol: FunctionSymbol) -> str:
        if isinstance(symbol.type.return_type, (ArrayType, StructType)):
            raise CodegenError("aggregate return values are not supported by this compact backend")

        self.register_counter = 0
        self.label_counter = 0
        self.temp_counter = 0
        self.blocks = []
        self.entry_allocas = []
        self.storage = {}
        self.current_function = symbol
        entry = self._new_block("entry")

        parameters: list[str] = []
        for index, (parameter, type_) in enumerate(zip(declaration.parameters, symbol.type.parameters)):
            argument_name = f"%arg.{self._mangle(parameter.name)}.{index}"
            parameters.append(f"{self._parameter_type(type_)} {argument_name}")
            parameter_symbol = self.analysis.declarations.get(id(parameter))
            if not isinstance(parameter_symbol, VariableSymbol):
                raise CodegenError(f"missing parameter symbol for {parameter.name}")
            if self._is_aggregate(type_):
                slot = self._alloca(type_, parameter.name)
                self._copy_aggregate(slot, argument_name, type_)
                self.storage[parameter_symbol] = slot
            else:
                slot = self._alloca(type_, parameter.name)
                self._emit(f"store {self._llvm_type(type_)} {argument_name}, ptr {slot}, align {self._alignment(type_)}")
                self.storage[parameter_symbol] = slot

        self._emit_block_statement(declaration.body, create_scope=False)
        if not self._block().terminated:
            if symbol.type.return_type == VOID:
                self._terminate("ret void")
            else:
                self._terminate("unreachable")

        # All allocas are inserted at the start of entry so mem2reg can see them.
        entry.instructions[0:0] = self.entry_allocas
        header = (
            f"define {self._llvm_type(symbol.type.return_type)} @{self._mangle(declaration.name)}"
            f"({', '.join(parameters)}) {{"
        )
        output = [header]
        for block in self.blocks:
            output.append(f"{block.label}:")
            output.extend(f"  {instruction}" for instruction in block.instructions)
            if not block.terminated:
                output.append("  unreachable")
        output.append("}")
        output.append("")
        return "\n".join(output)

    def _emit_block_statement(self, block: ast.BlockStmt, create_scope: bool = True) -> None:
        # Storage is keyed by unique semantic symbols, so no explicit backend
        # scope stack is required. create_scope is retained to mirror the front end.
        _ = create_scope
        for statement in block.statements:
            if self._block().terminated:
                break
            self._emit_statement(statement)

    def _emit_statement(self, statement: ast.Stmt) -> None:
        if isinstance(statement, ast.BlockStmt):
            self._emit_block_statement(statement)
            return
        if isinstance(statement, ast.LetStmt):
            symbol = self.analysis.declarations.get(id(statement))
            if not isinstance(symbol, VariableSymbol):
                raise CodegenError(f"missing variable symbol for {statement.name}")
            value = self._emit_expression(statement.initializer)
            if self._is_aggregate(symbol.type):
                slot = self._alloca(symbol.type, statement.name)
                self._copy_aggregate(slot, value.operand, symbol.type)
            else:
                slot = self._alloca(symbol.type, statement.name)
                self._emit(
                    f"store {self._llvm_type(symbol.type)} {value.operand}, ptr {slot}, align {self._alignment(symbol.type)}"
                )
            self.storage[symbol] = slot
            return
        if isinstance(statement, ast.ExprStmt):
            self._emit_expression(statement.expression)
            return
        if isinstance(statement, ast.ReturnStmt):
            assert self.current_function is not None
            if statement.value is None:
                self._terminate("ret void")
            else:
                value = self._emit_expression(statement.value)
                self._terminate(f"ret {self._llvm_type(value.type)} {value.operand}")
            return
        if isinstance(statement, ast.IfStmt):
            self._emit_if(statement)
            return
        if isinstance(statement, ast.WhileStmt):
            self._emit_while(statement)
            return
        if isinstance(statement, ast.ForStmt):
            self._emit_for(statement)
            return
        raise CodegenError(f"unhandled statement {type(statement).__name__}")

    def _emit_if(self, statement: ast.IfStmt) -> None:
        condition = self._emit_expression(statement.condition)
        then_label = self._fresh_label("if.then")
        else_label = self._fresh_label("if.else")
        end_label = self._fresh_label("if.end")
        self._terminate(f"br i1 {condition.operand}, label %{then_label}, label %{else_label}")

        self._new_block(then_label)
        self._emit_block_statement(statement.then_branch)
        then_falls_through = not self._block().terminated
        if then_falls_through:
            self._terminate(f"br label %{end_label}")

        self._new_block(else_label)
        if isinstance(statement.else_branch, ast.BlockStmt):
            self._emit_block_statement(statement.else_branch)
        elif isinstance(statement.else_branch, ast.IfStmt):
            self._emit_statement(statement.else_branch)
        else:
            pass
        else_falls_through = not self._block().terminated
        if else_falls_through:
            self._terminate(f"br label %{end_label}")

        self._new_block(end_label)
        if not then_falls_through and not else_falls_through:
            self._terminate("unreachable")

    def _emit_while(self, statement: ast.WhileStmt) -> None:
        condition_label = self._fresh_label("while.cond")
        body_label = self._fresh_label("while.body")
        end_label = self._fresh_label("while.end")
        self._terminate(f"br label %{condition_label}")

        self._new_block(condition_label)
        condition = self._emit_expression(statement.condition)
        self._terminate(f"br i1 {condition.operand}, label %{body_label}, label %{end_label}")

        self._new_block(body_label)
        self._emit_block_statement(statement.body)
        if not self._block().terminated:
            self._terminate(f"br label %{condition_label}")

        self._new_block(end_label)

    def _emit_for(self, statement: ast.ForStmt) -> None:
        if statement.initializer is not None:
            self._emit_statement(statement.initializer)
        condition_label = self._fresh_label("for.cond")
        body_label = self._fresh_label("for.body")
        increment_label = self._fresh_label("for.inc")
        end_label = self._fresh_label("for.end")
        self._terminate(f"br label %{condition_label}")

        self._new_block(condition_label)
        if statement.condition is None:
            condition = _Value(BOOL, "true")
        else:
            condition = self._emit_expression(statement.condition)
        self._terminate(f"br i1 {condition.operand}, label %{body_label}, label %{end_label}")

        self._new_block(body_label)
        self._emit_block_statement(statement.body)
        if not self._block().terminated:
            self._terminate(f"br label %{increment_label}")

        self._new_block(increment_label)
        if statement.increment is not None:
            self._emit_expression(statement.increment)
        if not self._block().terminated:
            self._terminate(f"br label %{condition_label}")

        self._new_block(end_label)

    def _emit_expression(self, expression: ast.Expr) -> _Value:
        type_ = self.analysis.type_of(expression)
        if type_.is_error:
            raise CodegenError(f"cannot generate code for erroneous expression {type(expression).__name__}")
        if isinstance(expression, ast.IntegerExpr):
            return _Value(INT, str(expression.value))
        if isinstance(expression, ast.BooleanExpr):
            return _Value(BOOL, "true" if expression.value else "false")
        if isinstance(expression, ast.StringExpr):
            name, length = self._intern_string(expression.value)
            register = self._register()
            self._emit(
                f"{register} = getelementptr inbounds [{length} x i8], ptr {name}, i64 0, i64 0"
            )
            return _Value(STRING, register)
        if isinstance(expression, ast.ArrayExpr):
            assert isinstance(type_, ArrayType)
            pointer = self._alloca(type_, "array.literal")
            for index, element in enumerate(expression.elements):
                element_value = self._emit_expression(element)
                element_pointer = self._register()
                llvm_array = self._llvm_type(type_)
                self._emit(
                    f"{element_pointer} = getelementptr inbounds {llvm_array}, ptr {pointer}, i64 0, i64 {index}"
                )
                if self._is_aggregate(type_.element):
                    self._copy_aggregate(element_pointer, element_value.operand, type_.element)
                else:
                    self._emit(
                        f"store {self._llvm_type(type_.element)} {element_value.operand}, ptr {element_pointer}, "
                        f"align {self._alignment(type_.element)}"
                    )
            return _Value(type_, pointer)
        if isinstance(expression, ast.StructInitExpr):
            assert isinstance(type_, StructType)
            pointer = self._alloca(type_, f"{type_.name}.literal")
            by_name = {field.name: field.value for field in expression.fields}
            for index, (field_name, field_type) in enumerate(type_.fields):
                value = self._emit_expression(by_name[field_name])
                field_pointer = self._register()
                self._emit(
                    f"{field_pointer} = getelementptr inbounds {self._llvm_type(type_)}, ptr {pointer}, i32 0, i32 {index}"
                )
                if self._is_aggregate(field_type):
                    self._copy_aggregate(field_pointer, value.operand, field_type)
                else:
                    self._emit(
                        f"store {self._llvm_type(field_type)} {value.operand}, ptr {field_pointer}, "
                        f"align {self._alignment(field_type)}"
                    )
            return _Value(type_, pointer)
        if isinstance(expression, ast.NameExpr):
            symbol = self.analysis.bindings.get(id(expression))
            if isinstance(symbol, VariableSymbol):
                pointer = self.storage.get(symbol)
                if pointer is None:
                    raise CodegenError(f"no storage for variable {symbol.name}")
                if self._is_aggregate(symbol.type):
                    return _Value(symbol.type, pointer)
                register = self._register()
                self._emit(
                    f"{register} = load {self._llvm_type(symbol.type)}, ptr {pointer}, align {self._alignment(symbol.type)}"
                )
                return _Value(symbol.type, register)
            if isinstance(symbol, (FunctionSymbol, BuiltinSymbol)):
                return _Value(symbol.type or ERROR, f"@{self._mangle(symbol.name)}")
            raise CodegenError(f"unresolved name {expression.name}")
        if isinstance(expression, ast.UnaryExpr):
            operand = self._emit_expression(expression.operand)
            register = self._register()
            if expression.operator == "-":
                self._emit(f"{register} = sub i64 0, {operand.operand}")
                return _Value(INT, register)
            if expression.operator == "+":
                return operand
            if expression.operator == "!":
                self._emit(f"{register} = xor i1 {operand.operand}, true")
                return _Value(BOOL, register)
            raise CodegenError(f"unknown unary operator {expression.operator}")
        if isinstance(expression, ast.BinaryExpr):
            if expression.operator in {"&&", "||"}:
                return self._emit_short_circuit(expression)
            left = self._emit_expression(expression.left)
            right = self._emit_expression(expression.right)
            return self._emit_binary(expression.operator, left, right)
        if isinstance(expression, ast.AssignExpr):
            pointer, target_type = self._emit_lvalue(expression.target)
            value = self._emit_expression(expression.value)
            if self._is_aggregate(target_type):
                self._copy_aggregate(pointer, value.operand, target_type)
                return _Value(target_type, pointer)
            self._emit(
                f"store {self._llvm_type(target_type)} {value.operand}, ptr {pointer}, align {self._alignment(target_type)}"
            )
            return _Value(target_type, value.operand)
        if isinstance(expression, ast.IndexExpr):
            pointer, element_type = self._emit_lvalue(expression)
            if self._is_aggregate(element_type):
                return _Value(element_type, pointer)
            register = self._register()
            self._emit(
                f"{register} = load {self._llvm_type(element_type)}, ptr {pointer}, align {self._alignment(element_type)}"
            )
            return _Value(element_type, register)
        if isinstance(expression, ast.FieldExpr):
            pointer, field_type = self._emit_lvalue(expression)
            if self._is_aggregate(field_type):
                return _Value(field_type, pointer)
            register = self._register()
            self._emit(
                f"{register} = load {self._llvm_type(field_type)}, ptr {pointer}, align {self._alignment(field_type)}"
            )
            return _Value(field_type, register)
        if isinstance(expression, ast.CallExpr):
            return self._emit_call(expression)
        raise CodegenError(f"unhandled expression {type(expression).__name__}")

    def _emit_lvalue(self, expression: ast.Expr) -> tuple[str, Type]:
        if isinstance(expression, ast.NameExpr):
            symbol = self.analysis.bindings.get(id(expression))
            if not isinstance(symbol, VariableSymbol):
                raise CodegenError("name is not assignable")
            pointer = self.storage.get(symbol)
            if pointer is None:
                raise CodegenError(f"no storage for {symbol.name}")
            return pointer, symbol.type
        if isinstance(expression, ast.IndexExpr):
            collection = self._emit_expression(expression.collection)
            if not isinstance(collection.type, ArrayType):
                raise CodegenError("indexing non-array")
            index = self._emit_expression(expression.index)
            self._emit_bounds_check(index.operand, collection.type.length)
            pointer = self._register()
            self._emit(
                f"{pointer} = getelementptr inbounds {self._llvm_type(collection.type)}, ptr {collection.operand}, "
                f"i64 0, i64 {index.operand}"
            )
            return pointer, collection.type.element
        if isinstance(expression, ast.FieldExpr):
            receiver = self._emit_expression(expression.receiver)
            if not isinstance(receiver.type, StructType):
                raise CodegenError("field access on non-structure")
            index = receiver.type.field_index(expression.name)
            field_type = receiver.type.field_type(expression.name)
            if index is None or field_type is None:
                raise CodegenError(f"unknown field {expression.name}")
            pointer = self._register()
            self._emit(
                f"{pointer} = getelementptr inbounds {self._llvm_type(receiver.type)}, ptr {receiver.operand}, "
                f"i32 0, i32 {index}"
            )
            return pointer, field_type
        raise CodegenError("invalid lvalue")

    def _emit_call(self, expression: ast.CallExpr) -> _Value:
        if isinstance(expression.callee, ast.NameExpr):
            name = expression.callee.name
            if name == "len":
                argument = self._emit_expression(expression.arguments[0])
                if isinstance(argument.type, ArrayType):
                    return _Value(INT, str(argument.type.length))
                register = self._register()
                self._emit(f"{register} = call i64 @strlen(ptr {argument.operand})")
                return _Value(INT, register)
            if name == "print_int":
                value = self._emit_expression(expression.arguments[0])
                format_pointer = self._register()
                self._emit(
                    f"{format_pointer} = getelementptr inbounds [5 x i8], ptr @.fmt.int, i64 0, i64 0"
                )
                call_result = self._register()
                self._emit(f"{call_result} = call i32 (ptr, ...) @printf(ptr {format_pointer}, i64 {value.operand})")
                return _Value(VOID, "")
            if name == "print_string":
                value = self._emit_expression(expression.arguments[0])
                call_result = self._register()
                self._emit(f"{call_result} = call i32 @puts(ptr {value.operand})")
                return _Value(VOID, "")
            if name == "print_bool":
                value = self._emit_expression(expression.arguments[0])
                pointer = self._register()
                self._emit(f"{pointer} = select i1 {value.operand}, ptr @.bool.true, ptr @.bool.false")
                call_result = self._register()
                self._emit(f"{call_result} = call i32 @puts(ptr {pointer})")
                return _Value(VOID, "")
            if name == "assert":
                condition = self._emit_expression(expression.arguments[0])
                ok_label = self._fresh_label("assert.ok")
                fail_label = self._fresh_label("assert.fail")
                self._terminate(f"br i1 {condition.operand}, label %{ok_label}, label %{fail_label}")
                self._new_block(fail_label)
                message_pointer = self._register()
                self._emit(
                    f"{message_pointer} = getelementptr inbounds [26 x i8], ptr @.assert.msg, i64 0, i64 0"
                )
                ignored = self._register()
                self._emit(f"{ignored} = call i32 @puts(ptr {message_pointer})")
                self._emit("call void @abort()")
                self._terminate("unreachable")
                self._new_block(ok_label)
                return _Value(VOID, "")

        callee_symbol = None
        if isinstance(expression.callee, ast.NameExpr):
            callee_symbol = self.analysis.bindings.get(id(expression.callee))
        if not isinstance(callee_symbol, FunctionSymbol):
            raise CodegenError("LLVM backend supports direct function calls only")
        arguments: list[str] = []
        for argument_expression, parameter_type in zip(expression.arguments, callee_symbol.type.parameters):
            value = self._emit_expression(argument_expression)
            if self._is_aggregate(parameter_type):
                copy = self._alloca(parameter_type, "arg.copy")
                self._copy_aggregate(copy, value.operand, parameter_type)
                arguments.append(f"ptr {copy}")
            else:
                arguments.append(f"{self._llvm_type(parameter_type)} {value.operand}")
        return_type = callee_symbol.type.return_type
        if return_type == VOID:
            self._emit(f"call void @{self._mangle(callee_symbol.name)}({', '.join(arguments)})")
            return _Value(VOID, "")
        register = self._register()
        self._emit(
            f"{register} = call {self._llvm_type(return_type)} @{self._mangle(callee_symbol.name)}"
            f"({', '.join(arguments)})"
        )
        return _Value(return_type, register)

    def _emit_binary(self, operator: str, left: _Value, right: _Value) -> _Value:
        register = self._register()
        if operator == "+":
            self._emit(f"{register} = add i64 {left.operand}, {right.operand}")
            return _Value(INT, register)
        if operator == "-":
            self._emit(f"{register} = sub i64 {left.operand}, {right.operand}")
            return _Value(INT, register)
        if operator == "*":
            self._emit(f"{register} = mul i64 {left.operand}, {right.operand}")
            return _Value(INT, register)
        if operator in {"/", "%"}:
            self._emit_nonzero_check(right.operand)
            opcode = "sdiv" if operator == "/" else "srem"
            self._emit(f"{register} = {opcode} i64 {left.operand}, {right.operand}")
            return _Value(INT, register)
        comparisons = {"<": "slt", "<=": "sle", ">": "sgt", ">=": "sge"}
        if operator in comparisons:
            self._emit(f"{register} = icmp {comparisons[operator]} i64 {left.operand}, {right.operand}")
            return _Value(BOOL, register)
        if operator in {"==", "!="}:
            predicate = "eq" if operator == "==" else "ne"
            if left.type == STRING:
                comparison = self._register()
                self._emit(f"{comparison} = call i32 @strcmp(ptr {left.operand}, ptr {right.operand})")
                self._emit(f"{register} = icmp {predicate} i32 {comparison}, 0")
            else:
                self._emit(
                    f"{register} = icmp {predicate} {self._llvm_type(left.type)} {left.operand}, {right.operand}"
                )
            return _Value(BOOL, register)
        raise CodegenError(f"unknown binary operator {operator}")

    def _emit_short_circuit(self, expression: ast.BinaryExpr) -> _Value:
        left = self._emit_expression(expression.left)
        left_block = self._block().label
        rhs_label = self._fresh_label("logic.rhs")
        end_label = self._fresh_label("logic.end")
        if expression.operator == "&&":
            self._terminate(f"br i1 {left.operand}, label %{rhs_label}, label %{end_label}")
            short_value = "false"
        else:
            self._terminate(f"br i1 {left.operand}, label %{end_label}, label %{rhs_label}")
            short_value = "true"
        self._new_block(rhs_label)
        right = self._emit_expression(expression.right)
        right_block = self._block().label
        self._terminate(f"br label %{end_label}")
        self._new_block(end_label)
        result = self._register()
        self._emit(f"{result} = phi i1 [{short_value}, %{left_block}], [{right.operand}, %{right_block}]")
        return _Value(BOOL, result)

    def _emit_bounds_check(self, index: str, length: int) -> None:
        nonnegative = self._register()
        below_length = self._register()
        in_range = self._register()
        ok_label = self._fresh_label("index.ok")
        fail_label = self._fresh_label("index.fail")
        self._emit(f"{nonnegative} = icmp sge i64 {index}, 0")
        self._emit(f"{below_length} = icmp slt i64 {index}, {length}")
        self._emit(f"{in_range} = and i1 {nonnegative}, {below_length}")
        self._terminate(f"br i1 {in_range}, label %{ok_label}, label %{fail_label}")
        self._new_block(fail_label)
        self._emit("call void @abort()")
        self._terminate("unreachable")
        self._new_block(ok_label)

    def _emit_nonzero_check(self, divisor: str) -> None:
        nonzero = self._register()
        ok_label = self._fresh_label("div.ok")
        fail_label = self._fresh_label("div.zero")
        self._emit(f"{nonzero} = icmp ne i64 {divisor}, 0")
        self._terminate(f"br i1 {nonzero}, label %{ok_label}, label %{fail_label}")
        self._new_block(fail_label)
        self._emit("call void @abort()")
        self._terminate("unreachable")
        self._new_block(ok_label)

    def _copy_aggregate(self, destination: str, source: str, type_: Type) -> None:
        if isinstance(type_, ArrayType):
            for index in range(type_.length):
                dst = self._register()
                src = self._register()
                llvm_type = self._llvm_type(type_)
                self._emit(f"{dst} = getelementptr inbounds {llvm_type}, ptr {destination}, i64 0, i64 {index}")
                self._emit(f"{src} = getelementptr inbounds {llvm_type}, ptr {source}, i64 0, i64 {index}")
                if self._is_aggregate(type_.element):
                    self._copy_aggregate(dst, src, type_.element)
                else:
                    value = self._register()
                    element_llvm = self._llvm_type(type_.element)
                    align = self._alignment(type_.element)
                    self._emit(f"{value} = load {element_llvm}, ptr {src}, align {align}")
                    self._emit(f"store {element_llvm} {value}, ptr {dst}, align {align}")
            return
        if isinstance(type_, StructType):
            for index, (_, field_type) in enumerate(type_.fields):
                dst = self._register()
                src = self._register()
                llvm_type = self._llvm_type(type_)
                self._emit(f"{dst} = getelementptr inbounds {llvm_type}, ptr {destination}, i32 0, i32 {index}")
                self._emit(f"{src} = getelementptr inbounds {llvm_type}, ptr {source}, i32 0, i32 {index}")
                if self._is_aggregate(field_type):
                    self._copy_aggregate(dst, src, field_type)
                else:
                    value = self._register()
                    field_llvm = self._llvm_type(field_type)
                    align = self._alignment(field_type)
                    self._emit(f"{value} = load {field_llvm}, ptr {src}, align {align}")
                    self._emit(f"store {field_llvm} {value}, ptr {dst}, align {align}")
            return
        raise CodegenError(f"copy requested for non-aggregate type {type_.display()}")

    def _alloca(self, type_: Type, hint: str) -> str:
        name = f"%{self._mangle(hint)}.slot.{self.temp_counter}"
        self.temp_counter += 1
        self.entry_allocas.append(
            f"{name} = alloca {self._llvm_type(type_)}, align {self._alignment(type_)}"
        )
        return name

    def _intern_string(self, value: str) -> tuple[str, int]:
        existing = self.string_globals.get(value)
        if existing is not None:
            return existing
        name = f"@.str.{len(self.string_globals)}"
        length = len(value.encode("utf-8")) + 1
        result = (name, length)
        self.string_globals[value] = result
        self.string_order.append(value)
        return result

    def _new_block(self, label: str) -> _Block:
        block = _Block(label)
        self.blocks.append(block)
        self.current = block
        return block

    def _block(self) -> _Block:
        if self.current is None:
            raise CodegenError("no current basic block")
        return self.current

    def _emit(self, instruction: str) -> None:
        block = self._block()
        if block.terminated:
            raise CodegenError(f"cannot emit after terminator in block {block.label}")
        block.instructions.append(instruction)

    def _terminate(self, instruction: str) -> None:
        self._emit(instruction)
        self._block().terminated = True

    def _register(self) -> str:
        value = f"%r{self.register_counter}"
        self.register_counter += 1
        return value

    def _fresh_label(self, prefix: str) -> str:
        value = f"{prefix}.{self.label_counter}"
        self.label_counter += 1
        return value

    def _llvm_type(self, type_: Type) -> str:
        if type_ == INT:
            return "i64"
        if type_ == BOOL:
            return "i1"
        if type_ == STRING:
            return "ptr"
        if type_ == VOID:
            return "void"
        if isinstance(type_, ArrayType):
            return f"[{type_.length} x {self._llvm_type(type_.element)}]"
        if isinstance(type_, StructType):
            return f"%struct.{self._mangle(type_.name)}"
        if isinstance(type_, FunctionType):
            return "ptr"
        raise CodegenError(f"unsupported type {type_.display()}")

    def _parameter_type(self, type_: Type) -> str:
        return "ptr" if self._is_aggregate(type_) else self._llvm_type(type_)

    @staticmethod
    def _is_aggregate(type_: Type) -> bool:
        return isinstance(type_, (ArrayType, StructType))

    def _alignment(self, type_: Type) -> int:
        if type_ == BOOL:
            return 1
        if type_ in {INT, STRING}:
            return 8
        if isinstance(type_, ArrayType):
            return self._alignment(type_.element)
        if isinstance(type_, StructType):
            return max((self._alignment(field) for _, field in type_.fields), default=1)
        return 8

    @staticmethod
    def _mangle(name: str) -> str:
        output: list[str] = []
        for character in name:
            if character.isalnum() or character in "._":
                output.append(character)
            else:
                output.append(f"_{ord(character):x}_")
        return "".join(output) or "anonymous"

    @staticmethod
    def _escape_identifier(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    @staticmethod
    def _llvm_c_string(value: str) -> str:
        data = value.encode("utf-8") + b"\x00"
        output: list[str] = []
        for byte in data:
            if 32 <= byte <= 126 and byte not in {34, 92}:
                output.append(chr(byte))
            else:
                output.append(f"\\{byte:02X}")
        return "".join(output)
