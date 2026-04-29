"""Analisador léxico para o subconjunto de Fortran 77.

Este ficheiro será implementado na Fase 1 com ply.lex.
"""

import ply.lex as lex


reserved = {
    "PROGRAM": "PROGRAM",
    "END": "END",
    "INTEGER": "INTEGER",
    "REAL": "REAL",
    "LOGICAL": "LOGICAL",
    "IF": "IF",
    "THEN": "THEN",
    "ELSE": "ELSE",
    "ENDIF": "ENDIF",
    "DO": "DO",
    "CONTINUE": "CONTINUE",
    "GOTO": "GOTO",
    "READ": "READ",
    "PRINT": "PRINT",
    "FUNCTION": "FUNCTION",
    "RETURN": "RETURN",
    "MOD": "MOD",
}


tokens = [
    "ID",
    "INTEGER_LITERAL",
    "REAL_LITERAL",
    "STRING_LITERAL",
    "BOOL_LITERAL",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "ASSIGN",
    "COMMA",
    "LPAREN",
    "RPAREN",
    "REL_OP",
    "LOGICAL_OP",
    "NOT_OP",
] + list(reserved.values())


# As regras concretas serão adicionadas na Fase 1.


def build_lexer(**kwargs):
    """Constrói o lexer.

    A implementação completa será feita na Fase 1.
    """
    raise NotImplementedError("Lexer ainda não implementado. Próxima fase: Fase 1.")
