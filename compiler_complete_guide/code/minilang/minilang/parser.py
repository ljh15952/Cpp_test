"""Recursive-descent and precedence-climbing parser for MiniLang."""
from __future__ import annotations

from . import ast
from .diagnostics import DiagnosticBag
from .token import SourceSpan, Token, TokenKind


class Parser:
    def __init__(self, tokens: tuple[Token, ...]) -> None:
        self.tokens = tokens
        self.index = 0
        self.diagnostics = DiagnosticBag()

    def parse_program(self) -> ast.Program:
        declarations: list[ast.Decl] = []
        start = self.current.span
        while not self._check(TokenKind.EOF):
            before = self.index
            declaration = self._parse_declaration()
            if declaration is not None:
                declarations.append(declaration)
            if self.index == before:
                self._advance()
        end = self.current.span
        return ast.Program(tuple(declarations), SourceSpan.covering(start, end))

    @property
    def current(self) -> Token:
        return self.tokens[min(self.index, len(self.tokens) - 1)]

    @property
    def previous(self) -> Token:
        return self.tokens[max(0, self.index - 1)]

    def _parse_declaration(self) -> ast.Decl | None:
        if self._match(TokenKind.STRUCT):
            return self._parse_struct_declaration(self.previous)
        if self._match(TokenKind.FN):
            return self._parse_function_declaration(self.previous)
        self._error(self.current, "PAR001", "top-level declaration must start with 'struct' or 'fn'")
        self._synchronize_declaration()
        return None

    def _parse_struct_declaration(self, start: Token) -> ast.StructDecl:
        name = self._expect(TokenKind.IDENTIFIER, "PAR002", "expected structure name")
        self._expect(TokenKind.LEFT_BRACE, "PAR003", "expected '{' after structure name")
        fields: list[ast.StructField] = []
        seen: set[str] = set()
        while not self._check(TokenKind.RIGHT_BRACE) and not self._check(TokenKind.EOF):
            field_name = self._expect(TokenKind.IDENTIFIER, "PAR004", "expected field name")
            self._expect(TokenKind.COLON, "PAR005", "expected ':' after field name")
            type_syntax = self._parse_type()
            semi = self._expect(TokenKind.SEMICOLON, "PAR006", "expected ';' after field declaration")
            if field_name.lexeme in seen:
                self._error(field_name, "PAR007", f"duplicate field {field_name.lexeme!r}")
            seen.add(field_name.lexeme)
            fields.append(
                ast.StructField(
                    field_name.lexeme,
                    type_syntax,
                    SourceSpan.covering(field_name.span, semi.span),
                )
            )
        close = self._expect(TokenKind.RIGHT_BRACE, "PAR008", "expected '}' after structure declaration")
        return ast.StructDecl(name.lexeme, tuple(fields), SourceSpan.covering(start.span, close.span))

    def _parse_function_declaration(self, start: Token) -> ast.FunctionDecl:
        name = self._expect(TokenKind.IDENTIFIER, "PAR009", "expected function name")
        self._expect(TokenKind.LEFT_PAREN, "PAR010", "expected '(' after function name")
        parameters: list[ast.Parameter] = []
        if not self._check(TokenKind.RIGHT_PAREN):
            while True:
                param_name = self._expect(TokenKind.IDENTIFIER, "PAR011", "expected parameter name")
                self._expect(TokenKind.COLON, "PAR012", "expected ':' after parameter name")
                type_syntax = self._parse_type()
                parameters.append(
                    ast.Parameter(
                        param_name.lexeme,
                        type_syntax,
                        SourceSpan.covering(param_name.span, type_syntax.span),
                    )
                )
                if not self._match(TokenKind.COMMA):
                    break
        self._expect(TokenKind.RIGHT_PAREN, "PAR013", "expected ')' after parameters")
        if self._match(TokenKind.ARROW):
            return_type = self._parse_type()
        else:
            token = self.previous
            return_type = ast.TypeSyntax(token.span, name="void")
        body = self._parse_block()
        return ast.FunctionDecl(
            name.lexeme,
            tuple(parameters),
            return_type,
            body,
            SourceSpan.covering(start.span, body.span),
        )

    def _parse_type(self) -> ast.TypeSyntax:
        if self._match(TokenKind.LEFT_BRACKET):
            start = self.previous
            element = self._parse_type()
            self._expect(TokenKind.SEMICOLON, "PAR014", "expected ';' between array element type and length")
            length_token = self._expect(TokenKind.INTEGER, "PAR015", "expected array length")
            close = self._expect(TokenKind.RIGHT_BRACKET, "PAR016", "expected ']' after array type")
            length = int(length_token.literal) if isinstance(length_token.literal, int) else 0
            if length <= 0:
                self._error(length_token, "PAR017", "array length must be positive")
            return ast.TypeSyntax(SourceSpan.covering(start.span, close.span), element=element, length=max(0, length))

        names = {
            TokenKind.INT: "int",
            TokenKind.BOOL: "bool",
            TokenKind.STRING_TYPE: "string",
            TokenKind.VOID: "void",
        }
        if self.current.kind in names:
            token = self._advance()
            return ast.TypeSyntax(token.span, name=names[token.kind])
        if self._match(TokenKind.IDENTIFIER):
            token = self.previous
            return ast.TypeSyntax(token.span, name=token.lexeme)
        token = self.current
        self._error(token, "PAR018", "expected a type")
        self._advance_if_not_eof()
        return ast.TypeSyntax(token.span, name="<error>")

    def _parse_block(self) -> ast.BlockStmt:
        open_brace = self._expect(TokenKind.LEFT_BRACE, "PAR019", "expected '{' to start block")
        statements: list[ast.Stmt] = []
        while not self._check(TokenKind.RIGHT_BRACE) and not self._check(TokenKind.EOF):
            before = self.index
            statements.append(self._parse_statement())
            if self.index == before:
                self._advance()
        close = self._expect(TokenKind.RIGHT_BRACE, "PAR020", "expected '}' after block")
        return ast.BlockStmt(tuple(statements), SourceSpan.covering(open_brace.span, close.span))

    def _parse_statement(self) -> ast.Stmt:
        if self._match(TokenKind.LET):
            return self._parse_let_statement(self.previous)
        if self._match(TokenKind.IF):
            return self._parse_if_statement(self.previous)
        if self._match(TokenKind.WHILE):
            return self._parse_while_statement(self.previous)
        if self._match(TokenKind.FOR):
            return self._parse_for_statement(self.previous)
        if self._match(TokenKind.RETURN):
            return self._parse_return_statement(self.previous)
        if self._check(TokenKind.LEFT_BRACE):
            return self._parse_block()
        expression = self._parse_expression()
        semi = self._expect(TokenKind.SEMICOLON, "PAR021", "expected ';' after expression")
        return ast.ExprStmt(expression, SourceSpan.covering(expression.span, semi.span))

    def _parse_let_statement(self, start: Token) -> ast.LetStmt:
        name = self._expect(TokenKind.IDENTIFIER, "PAR022", "expected variable name")
        type_syntax: ast.TypeSyntax | None = None
        if self._match(TokenKind.COLON):
            type_syntax = self._parse_type()
        self._expect(TokenKind.EQUAL, "PAR023", "expected '=' in variable declaration")
        initializer = self._parse_expression()
        semi = self._expect(TokenKind.SEMICOLON, "PAR024", "expected ';' after variable declaration")
        return ast.LetStmt(name.lexeme, type_syntax, initializer, SourceSpan.covering(start.span, semi.span))

    def _parse_if_statement(self, start: Token) -> ast.IfStmt:
        self._expect(TokenKind.LEFT_PAREN, "PAR025", "expected '(' after 'if'")
        condition = self._parse_expression()
        self._expect(TokenKind.RIGHT_PAREN, "PAR026", "expected ')' after if condition")
        then_branch = self._parse_block()
        else_branch: ast.BlockStmt | ast.IfStmt | None = None
        if self._match(TokenKind.ELSE):
            if self._match(TokenKind.IF):
                else_branch = self._parse_if_statement(self.previous)
            else:
                else_branch = self._parse_block()
        end_span = else_branch.span if else_branch is not None else then_branch.span
        return ast.IfStmt(condition, then_branch, else_branch, SourceSpan.covering(start.span, end_span))

    def _parse_while_statement(self, start: Token) -> ast.WhileStmt:
        self._expect(TokenKind.LEFT_PAREN, "PAR027", "expected '(' after 'while'")
        condition = self._parse_expression()
        self._expect(TokenKind.RIGHT_PAREN, "PAR028", "expected ')' after while condition")
        body = self._parse_block()
        return ast.WhileStmt(condition, body, SourceSpan.covering(start.span, body.span))

    def _parse_for_statement(self, start: Token) -> ast.ForStmt:
        self._expect(TokenKind.LEFT_PAREN, "PAR029", "expected '(' after 'for'")
        initializer: ast.Stmt | None
        if self._match(TokenKind.SEMICOLON):
            initializer = None
        elif self._match(TokenKind.LET):
            initializer = self._parse_let_statement(self.previous)
        else:
            expression = self._parse_expression()
            semi = self._expect(TokenKind.SEMICOLON, "PAR030", "expected ';' after for initializer")
            initializer = ast.ExprStmt(expression, SourceSpan.covering(expression.span, semi.span))

        condition = None if self._check(TokenKind.SEMICOLON) else self._parse_expression()
        self._expect(TokenKind.SEMICOLON, "PAR031", "expected ';' after for condition")
        increment = None if self._check(TokenKind.RIGHT_PAREN) else self._parse_expression()
        self._expect(TokenKind.RIGHT_PAREN, "PAR032", "expected ')' after for clauses")
        body = self._parse_block()
        return ast.ForStmt(initializer, condition, increment, body, SourceSpan.covering(start.span, body.span))

    def _parse_return_statement(self, start: Token) -> ast.ReturnStmt:
        value = None if self._check(TokenKind.SEMICOLON) else self._parse_expression()
        semi = self._expect(TokenKind.SEMICOLON, "PAR033", "expected ';' after return statement")
        return ast.ReturnStmt(value, SourceSpan.covering(start.span, semi.span))

    def _parse_expression(self) -> ast.Expr:
        return self._parse_assignment()

    def _parse_assignment(self) -> ast.Expr:
        left = self._parse_or()
        if self._match(TokenKind.EQUAL):
            value = self._parse_assignment()
            if not isinstance(left, (ast.NameExpr, ast.IndexExpr, ast.FieldExpr)):
                self._error(self.previous, "PAR034", "invalid assignment target")
            return ast.AssignExpr(left, value, SourceSpan.covering(left.span, value.span))
        return left

    def _parse_or(self) -> ast.Expr:
        expression = self._parse_and()
        while self._match(TokenKind.OR_OR):
            operator = self.previous
            right = self._parse_and()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_and(self) -> ast.Expr:
        expression = self._parse_equality()
        while self._match(TokenKind.AND_AND):
            operator = self.previous
            right = self._parse_equality()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_equality(self) -> ast.Expr:
        expression = self._parse_comparison()
        while self._match(TokenKind.EQUAL_EQUAL, TokenKind.BANG_EQUAL):
            operator = self.previous
            right = self._parse_comparison()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_comparison(self) -> ast.Expr:
        expression = self._parse_term()
        while self._match(TokenKind.LESS, TokenKind.LESS_EQUAL, TokenKind.GREATER, TokenKind.GREATER_EQUAL):
            operator = self.previous
            right = self._parse_term()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_term(self) -> ast.Expr:
        expression = self._parse_factor()
        while self._match(TokenKind.PLUS, TokenKind.MINUS):
            operator = self.previous
            right = self._parse_factor()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_factor(self) -> ast.Expr:
        expression = self._parse_unary()
        while self._match(TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT):
            operator = self.previous
            right = self._parse_unary()
            expression = ast.BinaryExpr(expression, operator.lexeme, right, SourceSpan.covering(expression.span, right.span))
        return expression

    def _parse_unary(self) -> ast.Expr:
        if self._match(TokenKind.BANG, TokenKind.MINUS, TokenKind.PLUS):
            operator = self.previous
            operand = self._parse_unary()
            return ast.UnaryExpr(operator.lexeme, operand, SourceSpan.covering(operator.span, operand.span))
        return self._parse_postfix()

    def _parse_postfix(self) -> ast.Expr:
        expression = self._parse_primary()
        while True:
            if self._match(TokenKind.LEFT_PAREN):
                arguments: list[ast.Expr] = []
                if not self._check(TokenKind.RIGHT_PAREN):
                    while True:
                        arguments.append(self._parse_expression())
                        if not self._match(TokenKind.COMMA):
                            break
                close = self._expect(TokenKind.RIGHT_PAREN, "PAR035", "expected ')' after arguments")
                expression = ast.CallExpr(expression, tuple(arguments), SourceSpan.covering(expression.span, close.span))
            elif self._match(TokenKind.LEFT_BRACKET):
                index = self._parse_expression()
                close = self._expect(TokenKind.RIGHT_BRACKET, "PAR036", "expected ']' after index")
                expression = ast.IndexExpr(expression, index, SourceSpan.covering(expression.span, close.span))
            elif self._match(TokenKind.DOT):
                name = self._expect(TokenKind.IDENTIFIER, "PAR037", "expected field name after '.'")
                expression = ast.FieldExpr(expression, name.lexeme, SourceSpan.covering(expression.span, name.span))
            else:
                break
        return expression

    def _parse_primary(self) -> ast.Expr:
        if self._match(TokenKind.INTEGER):
            token = self.previous
            return ast.IntegerExpr(int(token.literal), token.span)
        if self._match(TokenKind.STRING):
            token = self.previous
            return ast.StringExpr(str(token.literal), token.span)
        if self._match(TokenKind.TRUE):
            return ast.BooleanExpr(True, self.previous.span)
        if self._match(TokenKind.FALSE):
            return ast.BooleanExpr(False, self.previous.span)
        if self._match(TokenKind.LEFT_PAREN):
            open_token = self.previous
            expression = self._parse_expression()
            close = self._expect(TokenKind.RIGHT_PAREN, "PAR038", "expected ')' after expression")
            # Parentheses do not need a separate AST node, but their span is
            # intentionally not discarded from diagnostics at this level.
            _ = SourceSpan.covering(open_token.span, close.span)
            return expression
        if self._match(TokenKind.LEFT_BRACKET):
            open_token = self.previous
            elements: list[ast.Expr] = []
            if not self._check(TokenKind.RIGHT_BRACKET):
                while True:
                    elements.append(self._parse_expression())
                    if not self._match(TokenKind.COMMA):
                        break
            close = self._expect(TokenKind.RIGHT_BRACKET, "PAR039", "expected ']' after array literal")
            return ast.ArrayExpr(tuple(elements), SourceSpan.covering(open_token.span, close.span))
        if self._match(TokenKind.IDENTIFIER):
            name = self.previous
            if self._match(TokenKind.LEFT_BRACE):
                fields: list[ast.StructInitField] = []
                if not self._check(TokenKind.RIGHT_BRACE):
                    while True:
                        field_name = self._expect(TokenKind.IDENTIFIER, "PAR040", "expected field name")
                        self._expect(TokenKind.COLON, "PAR041", "expected ':' after field name")
                        value = self._parse_expression()
                        fields.append(
                            ast.StructInitField(
                                field_name.lexeme,
                                value,
                                SourceSpan.covering(field_name.span, value.span),
                            )
                        )
                        if not self._match(TokenKind.COMMA):
                            break
                close = self._expect(TokenKind.RIGHT_BRACE, "PAR042", "expected '}' after structure initializer")
                return ast.StructInitExpr(name.lexeme, tuple(fields), SourceSpan.covering(name.span, close.span))
            return ast.NameExpr(name.lexeme, name.span)

        token = self.current
        self._error(token, "PAR043", f"expected expression, found {token.kind.name}")
        self._advance_if_not_eof()
        return ast.ErrorExpr(token.span)

    def _expect(self, kind: TokenKind, code: str, message: str) -> Token:
        if self._check(kind):
            return self._advance()
        self._error(self.current, code, message)
        # Synthetic zero-width token anchors recovery at the current location.
        return Token(kind, "", None, self.current.span)

    def _error(self, token: Token, code: str, message: str) -> None:
        self.diagnostics.error(code, message, token.span)

    def _synchronize_declaration(self) -> None:
        while not self._check(TokenKind.EOF):
            if self.current.kind in {TokenKind.FN, TokenKind.STRUCT}:
                return
            self._advance()

    def _advance_if_not_eof(self) -> None:
        if not self._check(TokenKind.EOF):
            self._advance()

    def _match(self, *kinds: TokenKind) -> bool:
        if self.current.kind not in kinds:
            return False
        self._advance()
        return True

    def _check(self, kind: TokenKind) -> bool:
        return self.current.kind is kind

    def _advance(self) -> Token:
        token = self.current
        if token.kind is not TokenKind.EOF:
            self.index += 1
        return token
