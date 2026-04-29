"""Erros usados pelas fases do compilador."""


class CompilerError(Exception):
    """Erro base do compilador."""


class LexicalError(CompilerError):
    """Erro encontrado durante a análise léxica."""


class SyntaxErrorPL(CompilerError):
    """Erro encontrado durante a análise sintática."""


class SemanticError(CompilerError):
    """Erro encontrado durante a análise semântica."""
