"""Public compilation pipeline used by the CLI, tests, and book examples."""
from __future__ import annotations

from dataclasses import dataclass

from . import ast
from .diagnostics import Diagnostic
from .lexer import Lexer
from .optimizer import AstOptimizer, OptimizationStats
from .parser import Parser
from .semantic import AnalysisResult, SemanticAnalyzer


@dataclass(frozen=True, slots=True)
class CompilationUnit:
    source: str
    tokens: tuple
    program: ast.Program
    analysis: AnalysisResult
    diagnostics: tuple[Diagnostic, ...]
    optimization_stats: OptimizationStats | None = None

    @property
    def succeeded(self) -> bool:
        return not self.diagnostics


def compile_source(source: str, *, optimize: bool = False) -> CompilationUnit:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse_program()
    diagnostics: list[Diagnostic] = [*lexer.diagnostics.items, *parser.diagnostics.items]

    analysis = SemanticAnalyzer(program).analyze()
    diagnostics.extend(analysis.diagnostics)
    optimization_stats: OptimizationStats | None = None

    if optimize and not diagnostics:
        optimizer = AstOptimizer()
        program = optimizer.optimize(program)
        analysis = SemanticAnalyzer(program).analyze()
        diagnostics.extend(analysis.diagnostics)
        optimization_stats = optimizer.stats

    return CompilationUnit(
        source,
        tokens,
        program,
        analysis,
        tuple(diagnostics),
        optimization_stats,
    )
