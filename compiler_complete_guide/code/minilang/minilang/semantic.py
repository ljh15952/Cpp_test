"""Name resolution and static type checking for MiniLang."""
from __future__ import annotations

from dataclasses import dataclass

from . import ast
from .diagnostics import DiagnosticBag
from .symbols import (
    BuiltinSymbol,
    FunctionSymbol,
    Scope,
    StructSymbol,
    Symbol,
    SymbolKind,
    VariableSymbol,
)
from .typesys import (
    ArrayType,
    BOOL,
    ERROR,
    INT,
    STRING,
    VOID,
    FunctionType,
    StructType,
    Type,
    is_assignable,
    same_type,
)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    diagnostics: tuple
    node_types: dict[int, Type]
    bindings: dict[int, Symbol]
    declarations: dict[int, Symbol]
    functions: dict[str, FunctionSymbol]
    structs: dict[str, StructSymbol]

    def type_of(self, node: ast.Node) -> Type:
        return self.node_types.get(id(node), ERROR)

    def binding_of(self, node: ast.Node) -> Symbol | None:
        return self.bindings.get(id(node))


class SemanticAnalyzer:
    def __init__(self, program: ast.Program) -> None:
        self.program = program
        self.diagnostics = DiagnosticBag()
        self.node_types: dict[int, Type] = {}
        self.bindings: dict[int, Symbol] = {}
        self.declarations: dict[int, Symbol] = {}
        self.functions: dict[str, FunctionSymbol] = {}
        self.structs: dict[str, StructSymbol] = {}
        self.struct_declarations: dict[str, ast.StructDecl] = {}
        self.struct_states: dict[str, str] = {}
        self.global_scope = Scope()
        self.scope = self.global_scope
        self.current_function: FunctionSymbol | None = None
        self._install_builtins()

    def analyze(self) -> AnalysisResult:
        self._collect_struct_names()
        self._resolve_structs()
        self._collect_functions()
        for declaration in self.program.declarations:
            if isinstance(declaration, ast.FunctionDecl):
                symbol = self.functions.get(declaration.name)
                if symbol is not None and symbol.declaration is declaration:
                    self._analyze_function(declaration, symbol)
        return AnalysisResult(
            self.diagnostics.items,
            dict(self.node_types),
            dict(self.bindings),
            dict(self.declarations),
            dict(self.functions),
            dict(self.structs),
        )

    def _install_builtins(self) -> None:
        builtins: tuple[tuple[str, FunctionType | None], ...] = (
            ("print_int", FunctionType((INT,), VOID)),
            ("print_bool", FunctionType((BOOL,), VOID)),
            ("print_string", FunctionType((STRING,), VOID)),
            ("assert", FunctionType((BOOL,), VOID)),
            # len is intentionally overloaded and checked specially.
            ("len", None),
        )
        for name, function_type in builtins:
            self.global_scope.define(BuiltinSymbol(name, SymbolKind.BUILTIN, function_type))

    def _collect_struct_names(self) -> None:
        for declaration in self.program.declarations:
            if not isinstance(declaration, ast.StructDecl):
                continue
            if declaration.name in self.struct_declarations or self.global_scope.lookup_local(declaration.name):
                self.diagnostics.error(
                    "SEM001",
                    f"duplicate top-level name {declaration.name!r}",
                    declaration.span,
                )
                continue
            self.struct_declarations[declaration.name] = declaration
            self.struct_states[declaration.name] = "unresolved"

    def _resolve_structs(self) -> None:
        for name in tuple(self.struct_declarations):
            self._resolve_struct(name)
        for name, symbol in self.structs.items():
            self.global_scope.define(symbol)

    def _resolve_struct(self, name: str) -> StructType:
        existing = self.structs.get(name)
        if existing is not None:
            return existing.type
        state = self.struct_states.get(name)
        declaration = self.struct_declarations.get(name)
        if declaration is None:
            return ERROR  # type: ignore[return-value]
        if state == "resolving":
            self.diagnostics.error(
                "SEM002",
                f"recursive by-value structure {name!r} has infinite size",
                declaration.span,
            )
            return StructType(name, ())

        self.struct_states[name] = "resolving"
        fields: list[tuple[str, Type]] = []
        for field in declaration.fields:
            field_type = self._resolve_type_syntax(field.type_syntax, resolving_struct=name)
            if field_type == VOID:
                self.diagnostics.error("SEM003", "structure field cannot have type void", field.span)
                field_type = ERROR
            fields.append((field.name, field_type))
        type_ = StructType(name, tuple(fields))
        symbol = StructSymbol(name, SymbolKind.STRUCT, type_, declaration)
        self.structs[name] = symbol
        self.declarations[id(declaration)] = symbol
        self.struct_states[name] = "resolved"
        return type_

    def _collect_functions(self) -> None:
        for declaration in self.program.declarations:
            if not isinstance(declaration, ast.FunctionDecl):
                continue
            if self.global_scope.lookup_local(declaration.name) is not None:
                self.diagnostics.error(
                    "SEM004",
                    f"duplicate top-level name {declaration.name!r}",
                    declaration.span,
                )
                continue
            parameter_types = tuple(self._resolve_type_syntax(p.type_syntax) for p in declaration.parameters)
            return_type = self._resolve_type_syntax(declaration.return_type)
            if isinstance(return_type, (ArrayType, StructType)):
                self.diagnostics.error(
                    "SEM040",
                    "MiniLang 1.0 functions return only int, bool, string, or void; pass aggregates by value as parameters",
                    declaration.return_type.span,
                )
            if any(type_ == VOID for type_ in parameter_types):
                self.diagnostics.error("SEM005", "parameter cannot have type void", declaration.span)
            function_type = FunctionType(parameter_types, return_type)
            symbol = FunctionSymbol(declaration.name, SymbolKind.FUNCTION, function_type, declaration)
            self.functions[declaration.name] = symbol
            self.declarations[id(declaration)] = symbol
            self.global_scope.define(symbol)

        main = self.functions.get("main")
        if main is None:
            self.diagnostics.error("SEM006", "program must define fn main() -> int", self.program.span)
        elif main.type.parameters or main.type.return_type != INT:
            self.diagnostics.error("SEM007", "main must have type fn() -> int", main.declaration.span)

    def _analyze_function(self, declaration: ast.FunctionDecl, symbol: FunctionSymbol) -> None:
        previous_function = self.current_function
        previous_scope = self.scope
        self.current_function = symbol
        self.scope = Scope(self.global_scope)
        seen: set[str] = set()
        for parameter, parameter_type in zip(declaration.parameters, symbol.type.parameters):
            if parameter.name in seen:
                self.diagnostics.error("SEM008", f"duplicate parameter {parameter.name!r}", parameter.span)
                continue
            seen.add(parameter.name)
            parameter_symbol = VariableSymbol(
                parameter.name,
                SymbolKind.PARAMETER,
                parameter_type,
                mutable=True,
                depth=self.scope.depth,
            )
            self.scope.define(parameter_symbol)
            self.declarations[id(parameter)] = parameter_symbol
        self._analyze_block(declaration.body, create_scope=False)
        if symbol.type.return_type != VOID and not self._always_returns(declaration.body):
            self.diagnostics.error(
                "SEM009",
                f"function {declaration.name!r} may reach the end without returning {symbol.type.return_type.display()}",
                declaration.body.span,
            )
        self.scope = previous_scope
        self.current_function = previous_function

    def _analyze_block(self, block: ast.BlockStmt, create_scope: bool = True) -> None:
        previous = self.scope
        if create_scope:
            self.scope = Scope(previous)
        for statement in block.statements:
            self._analyze_statement(statement)
        if create_scope:
            self.scope = previous

    def _analyze_statement(self, statement: ast.Stmt) -> None:
        if isinstance(statement, ast.BlockStmt):
            self._analyze_block(statement)
        elif isinstance(statement, ast.LetStmt):
            value_type = self._analyze_expression(statement.initializer)
            declared_type = (
                self._resolve_type_syntax(statement.type_syntax)
                if statement.type_syntax is not None
                else value_type
            )
            if declared_type == VOID:
                self.diagnostics.error("SEM010", "variable cannot have type void", statement.span)
                declared_type = ERROR
            if not is_assignable(declared_type, value_type):
                self.diagnostics.error(
                    "SEM011",
                    f"cannot initialize {statement.name!r} of type {declared_type.display()} "
                    f"with {value_type.display()}",
                    statement.initializer.span,
                )
            symbol = VariableSymbol(
                statement.name,
                SymbolKind.VARIABLE,
                declared_type,
                mutable=True,
                depth=self.scope.depth,
            )
            if not self.scope.define(symbol):
                self.diagnostics.error(
                    "SEM012",
                    f"name {statement.name!r} is already declared in this scope",
                    statement.span,
                )
            self.declarations[id(statement)] = symbol
        elif isinstance(statement, ast.ExprStmt):
            self._analyze_expression(statement.expression)
        elif isinstance(statement, ast.IfStmt):
            self._require_bool(statement.condition, "if condition")
            self._analyze_block(statement.then_branch)
            if isinstance(statement.else_branch, ast.BlockStmt):
                self._analyze_block(statement.else_branch)
            elif isinstance(statement.else_branch, ast.IfStmt):
                self._analyze_statement(statement.else_branch)
        elif isinstance(statement, ast.WhileStmt):
            self._require_bool(statement.condition, "while condition")
            self._analyze_block(statement.body)
        elif isinstance(statement, ast.ForStmt):
            previous = self.scope
            self.scope = Scope(previous)
            if statement.initializer is not None:
                self._analyze_statement(statement.initializer)
            if statement.condition is not None:
                self._require_bool(statement.condition, "for condition")
            if statement.increment is not None:
                self._analyze_expression(statement.increment)
            self._analyze_block(statement.body)
            self.scope = previous
        elif isinstance(statement, ast.ReturnStmt):
            assert self.current_function is not None
            expected = self.current_function.type.return_type
            actual = VOID if statement.value is None else self._analyze_expression(statement.value)
            if not is_assignable(expected, actual):
                self.diagnostics.error(
                    "SEM013",
                    f"return type mismatch: expected {expected.display()}, got {actual.display()}",
                    statement.span,
                )
        else:
            raise AssertionError(f"unhandled statement: {type(statement).__name__}")

    def _analyze_expression(self, expression: ast.Expr) -> Type:
        if isinstance(expression, ast.IntegerExpr):
            return self._record_type(expression, INT)
        if isinstance(expression, ast.BooleanExpr):
            return self._record_type(expression, BOOL)
        if isinstance(expression, ast.StringExpr):
            return self._record_type(expression, STRING)
        if isinstance(expression, ast.ErrorExpr):
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.NameExpr):
            symbol = self.scope.lookup(expression.name)
            if symbol is None:
                self.diagnostics.error("SEM014", f"undefined name {expression.name!r}", expression.span)
                return self._record_type(expression, ERROR)
            self.bindings[id(expression)] = symbol
            if isinstance(symbol, VariableSymbol):
                return self._record_type(expression, symbol.type)
            if isinstance(symbol, (FunctionSymbol, BuiltinSymbol)):
                return self._record_type(expression, symbol.type or ERROR)
            self.diagnostics.error("SEM015", f"{expression.name!r} is a type, not a value", expression.span)
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.ArrayExpr):
            if not expression.elements:
                self.diagnostics.error(
                    "SEM016",
                    "cannot infer the type of an empty array literal; add an explicit variable type",
                    expression.span,
                )
                return self._record_type(expression, ArrayType(ERROR, 0))
            element_type = self._analyze_expression(expression.elements[0])
            for element in expression.elements[1:]:
                current = self._analyze_expression(element)
                if not same_type(element_type, current):
                    self.diagnostics.error(
                        "SEM017",
                        f"array element has type {current.display()}, expected {element_type.display()}",
                        element.span,
                    )
            return self._record_type(expression, ArrayType(element_type, len(expression.elements)))
        if isinstance(expression, ast.StructInitExpr):
            symbol = self.structs.get(expression.name)
            if symbol is None:
                self.diagnostics.error("SEM018", f"unknown structure {expression.name!r}", expression.span)
                for field in expression.fields:
                    self._analyze_expression(field.value)
                return self._record_type(expression, ERROR)
            supplied: dict[str, ast.StructInitField] = {}
            for field in expression.fields:
                if field.name in supplied:
                    self.diagnostics.error("SEM019", f"duplicate initializer for field {field.name!r}", field.span)
                supplied[field.name] = field
            for name, expected in symbol.type.fields:
                field = supplied.pop(name, None)
                if field is None:
                    self.diagnostics.error("SEM020", f"missing initializer for field {name!r}", expression.span)
                    continue
                actual = self._analyze_expression(field.value)
                if not is_assignable(expected, actual):
                    self.diagnostics.error(
                        "SEM021",
                        f"field {name!r} expects {expected.display()}, got {actual.display()}",
                        field.value.span,
                    )
            for unknown in supplied.values():
                self.diagnostics.error("SEM022", f"unknown field {unknown.name!r}", unknown.span)
                self._analyze_expression(unknown.value)
            self.bindings[id(expression)] = symbol
            return self._record_type(expression, symbol.type)
        if isinstance(expression, ast.UnaryExpr):
            operand = self._analyze_expression(expression.operand)
            if expression.operator in {"-", "+"}:
                self._expect_type(operand, INT, expression.operand, f"operator {expression.operator}")
                return self._record_type(expression, INT)
            if expression.operator == "!":
                self._expect_type(operand, BOOL, expression.operand, "operator !")
                return self._record_type(expression, BOOL)
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.BinaryExpr):
            left = self._analyze_expression(expression.left)
            right = self._analyze_expression(expression.right)
            op = expression.operator
            if op in {"+", "-", "*", "/", "%"}:
                self._expect_type(left, INT, expression.left, f"left operand of {op}")
                self._expect_type(right, INT, expression.right, f"right operand of {op}")
                return self._record_type(expression, INT)
            if op in {"<", "<=", ">", ">="}:
                self._expect_type(left, INT, expression.left, f"left operand of {op}")
                self._expect_type(right, INT, expression.right, f"right operand of {op}")
                return self._record_type(expression, BOOL)
            if op in {"&&", "||"}:
                self._expect_type(left, BOOL, expression.left, f"left operand of {op}")
                self._expect_type(right, BOOL, expression.right, f"right operand of {op}")
                return self._record_type(expression, BOOL)
            if op in {"==", "!="}:
                if not same_type(left, right):
                    self.diagnostics.error(
                        "SEM023",
                        f"cannot compare {left.display()} with {right.display()}",
                        expression.span,
                    )
                if not (left.is_scalar or left.is_error):
                    self.diagnostics.error("SEM024", "aggregate equality is not supported", expression.span)
                return self._record_type(expression, BOOL)
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.AssignExpr):
            target_type = self._analyze_lvalue(expression.target)
            value_type = self._analyze_expression(expression.value)
            if not is_assignable(target_type, value_type):
                self.diagnostics.error(
                    "SEM025",
                    f"cannot assign {value_type.display()} to {target_type.display()}",
                    expression.span,
                )
            return self._record_type(expression, target_type)
        if isinstance(expression, ast.CallExpr):
            if isinstance(expression.callee, ast.NameExpr) and expression.callee.name == "len":
                return self._analyze_len_call(expression)
            callee_type = self._analyze_expression(expression.callee)
            argument_types = [self._analyze_expression(arg) for arg in expression.arguments]
            if not isinstance(callee_type, FunctionType):
                if not callee_type.is_error:
                    self.diagnostics.error("SEM026", "attempted to call a non-function value", expression.callee.span)
                return self._record_type(expression, ERROR)
            if len(argument_types) != len(callee_type.parameters):
                self.diagnostics.error(
                    "SEM027",
                    f"expected {len(callee_type.parameters)} arguments, got {len(argument_types)}",
                    expression.span,
                )
            for index, (expected, actual) in enumerate(zip(callee_type.parameters, argument_types), 1):
                if not is_assignable(expected, actual):
                    self.diagnostics.error(
                        "SEM028",
                        f"argument {index}: expected {expected.display()}, got {actual.display()}",
                        expression.arguments[index - 1].span,
                    )
            return self._record_type(expression, callee_type.return_type)
        if isinstance(expression, ast.IndexExpr):
            collection = self._analyze_expression(expression.collection)
            index = self._analyze_expression(expression.index)
            self._expect_type(index, INT, expression.index, "array index")
            if isinstance(collection, ArrayType):
                return self._record_type(expression, collection.element)
            if not collection.is_error:
                self.diagnostics.error("SEM029", "indexing requires an array", expression.collection.span)
            return self._record_type(expression, ERROR)
        if isinstance(expression, ast.FieldExpr):
            receiver = self._analyze_expression(expression.receiver)
            if isinstance(receiver, StructType):
                field_type = receiver.field_type(expression.name)
                if field_type is None:
                    self.diagnostics.error(
                        "SEM030",
                        f"structure {receiver.name!r} has no field {expression.name!r}",
                        expression.span,
                    )
                    return self._record_type(expression, ERROR)
                return self._record_type(expression, field_type)
            if not receiver.is_error:
                self.diagnostics.error("SEM031", "field access requires a structure value", expression.receiver.span)
            return self._record_type(expression, ERROR)
        raise AssertionError(f"unhandled expression: {type(expression).__name__}")

    def _analyze_lvalue(self, expression: ast.Expr) -> Type:
        if isinstance(expression, ast.NameExpr):
            type_ = self._analyze_expression(expression)
            symbol = self.bindings.get(id(expression))
            if not isinstance(symbol, VariableSymbol):
                self.diagnostics.error("SEM032", "assignment target is not a variable", expression.span)
            return type_
        if isinstance(expression, ast.IndexExpr):
            return self._analyze_expression(expression)
        if isinstance(expression, ast.FieldExpr):
            return self._analyze_expression(expression)
        self.diagnostics.error("SEM033", "expression is not assignable", expression.span)
        return self._analyze_expression(expression)

    def _analyze_len_call(self, expression: ast.CallExpr) -> Type:
        # Record the callee binding even though len is overloaded.
        assert isinstance(expression.callee, ast.NameExpr)
        symbol = self.scope.lookup("len")
        if symbol is not None:
            self.bindings[id(expression.callee)] = symbol
        if len(expression.arguments) != 1:
            for argument in expression.arguments:
                self._analyze_expression(argument)
            self.diagnostics.error("SEM034", "len expects exactly one argument", expression.span)
            return self._record_type(expression, ERROR)
        argument_type = self._analyze_expression(expression.arguments[0])
        if not isinstance(argument_type, ArrayType) and argument_type != STRING and not argument_type.is_error:
            self.diagnostics.error("SEM035", "len accepts an array or string", expression.arguments[0].span)
        return self._record_type(expression, INT)

    def _require_bool(self, expression: ast.Expr, context: str) -> None:
        type_ = self._analyze_expression(expression)
        self._expect_type(type_, BOOL, expression, context)

    def _expect_type(self, actual: Type, expected: Type, node: ast.Node, context: str) -> None:
        if not same_type(actual, expected):
            self.diagnostics.error(
                "SEM036",
                f"{context} requires {expected.display()}, got {actual.display()}",
                node.span,
            )

    def _record_type(self, node: ast.Node, type_: Type) -> Type:
        self.node_types[id(node)] = type_
        return type_

    def _resolve_type_syntax(self, syntax: ast.TypeSyntax | None, resolving_struct: str | None = None) -> Type:
        if syntax is None:
            return ERROR
        if syntax.element is not None:
            element = self._resolve_type_syntax(syntax.element, resolving_struct=resolving_struct)
            if element == VOID:
                self.diagnostics.error("SEM037", "array element cannot have type void", syntax.span)
                return ERROR
            return ArrayType(element, syntax.length or 0)
        builtin = {"int": INT, "bool": BOOL, "string": STRING, "void": VOID, "<error>": ERROR}
        if syntax.name in builtin:
            return builtin[syntax.name]
        if syntax.name in self.struct_declarations:
            if syntax.name == resolving_struct and self.struct_states.get(syntax.name) == "resolving":
                declaration = self.struct_declarations[syntax.name]
                self.diagnostics.error(
                    "SEM038",
                    f"structure {syntax.name!r} cannot contain itself by value",
                    declaration.span,
                )
                return ERROR
            return self._resolve_struct(syntax.name)
        self.diagnostics.error("SEM039", f"unknown type {syntax.name!r}", syntax.span)
        return ERROR

    def _always_returns(self, statement: ast.Stmt) -> bool:
        if isinstance(statement, ast.ReturnStmt):
            return True
        if isinstance(statement, ast.BlockStmt):
            for child in statement.statements:
                if self._always_returns(child):
                    return True
            return False
        if isinstance(statement, ast.IfStmt):
            if statement.else_branch is None:
                return False
            return self._always_returns(statement.then_branch) and self._always_returns(statement.else_branch)
        return False
