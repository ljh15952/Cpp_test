from __future__ import annotations

import unittest

from minilang import ast
from minilang.ast_dump import dump
from minilang.driver import compile_source
from minilang.lexer import Lexer
from minilang.parser import Parser
from minilang.token import TokenKind


class LexerTests(unittest.TestCase):
    def test_keywords_identifiers_and_locations(self) -> None:
        source = "let 변수 = 0x2a + 0b10;\nreturn 변수;"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertFalse(lexer.diagnostics.has_errors)
        self.assertEqual(tokens[0].kind, TokenKind.LET)
        self.assertEqual(tokens[1].lexeme, "변수")
        self.assertEqual(tokens[3].literal, 42)
        self.assertEqual(tokens[5].literal, 2)
        self.assertEqual(tokens[7].span.start.line, 2)

    def test_nested_comments_and_string_escapes(self) -> None:
        source = '/* outer /* inner */ done */ "a\\n\\u{41}"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertFalse(lexer.diagnostics.has_errors)
        self.assertEqual(tokens[0].kind, TokenKind.STRING)
        self.assertEqual(tokens[0].literal, "a\nA")

    def test_invalid_input_produces_recoverable_tokens(self) -> None:
        lexer = Lexer('"unterminated\n@')
        tokens = lexer.tokenize()
        self.assertTrue(lexer.diagnostics.has_errors)
        self.assertEqual(tokens[0].kind, TokenKind.ERROR)
        self.assertEqual(tokens[1].kind, TokenKind.ERROR)
        self.assertEqual(tokens[-1].kind, TokenKind.EOF)


class ParserTests(unittest.TestCase):
    def parse(self, source: str) -> ast.Program:
        lexer = Lexer(source)
        parser = Parser(lexer.tokenize())
        program = parser.parse_program()
        self.assertFalse(lexer.diagnostics.has_errors, lexer.diagnostics.items)
        self.assertFalse(parser.diagnostics.has_errors, parser.diagnostics.items)
        return program

    def test_precedence(self) -> None:
        program = self.parse("fn main() -> int { return 1 + 2 * 3 == 7 || false; }")
        function = program.declarations[0]
        self.assertIsInstance(function, ast.FunctionDecl)
        return_stmt = function.body.statements[0]
        self.assertIsInstance(return_stmt, ast.ReturnStmt)
        expression = return_stmt.value
        self.assertIsInstance(expression, ast.BinaryExpr)
        self.assertEqual(expression.operator, "||")
        self.assertIsInstance(expression.left, ast.BinaryExpr)
        self.assertEqual(expression.left.operator, "==")

    def test_all_statement_forms(self) -> None:
        source = """
        fn main() -> int {
            let x: int = 0;
            while (x < 3) { x = x + 1; }
            for (let i: int = 0; i < 2; i = i + 1) { x = x + i; }
            if (x > 0) { return x; } else { return 0; }
        }
        """
        program = self.parse(source)
        function = program.declarations[0]
        self.assertEqual(len(function.body.statements), 4)
        self.assertIsInstance(function.body.statements[1], ast.WhileStmt)
        self.assertIsInstance(function.body.statements[2], ast.ForStmt)
        self.assertIsInstance(function.body.statements[3], ast.IfStmt)

    def test_ast_dump_is_deterministic(self) -> None:
        program = self.parse("fn main() -> int { return 42; }")
        text = dump(program)
        self.assertIn("Program", text)
        self.assertIn("IntegerExpr", text)
        self.assertNotIn("SourceSpan", text)


class SemanticTests(unittest.TestCase):
    def test_valid_program(self) -> None:
        source = """
        struct P { x: int; y: int; }
        fn length2(p: P) -> int { return p.x * p.x + p.y * p.y; }
        fn main() -> int {
            let p: P = P { x: 3, y: 4 };
            let xs: [int; 2] = [length2(p), 1];
            return xs[0];
        }
        """
        unit = compile_source(source)
        self.assertTrue(unit.succeeded, unit.diagnostics)

    def test_reports_multiple_errors(self) -> None:
        source = """
        struct P { x: int; }
        fn main() -> int {
            let p: P = P { y: 1 };
            let b: bool = 3;
            unknown = b + 1;
            return "bad";
        }
        """
        unit = compile_source(source)
        codes = {diagnostic.code for diagnostic in unit.diagnostics}
        self.assertGreaterEqual(len(unit.diagnostics), 5)
        self.assertIn("SEM020", codes)
        self.assertIn("SEM022", codes)
        self.assertIn("SEM011", codes)
        self.assertIn("SEM014", codes)
        self.assertIn("SEM013", codes)

    def test_scope_shadowing_is_legal_but_same_scope_duplicate_is_not(self) -> None:
        valid = compile_source("fn main() -> int { let x: int = 1; { let x: int = 2; } return x; }")
        self.assertTrue(valid.succeeded, valid.diagnostics)
        invalid = compile_source("fn main() -> int { let x: int = 1; let x: int = 2; return x; }")
        self.assertIn("SEM012", {diagnostic.code for diagnostic in invalid.diagnostics})


if __name__ == "__main__":
    unittest.main()
