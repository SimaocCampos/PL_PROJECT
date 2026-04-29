"""Analisador léxico para o subconjunto de Fortran 77.

O lexer usa ``ply.lex`` e reconhece a sintaxe necessária para os exemplos
iniciais do projeto: declarações, expressões, labels, ``IF``, ``DO``,
``GOTO``, ``READ`` e ``PRINT``.

Fortran não distingue maiúsculas de minúsculas. Por isso, identificadores e
palavras reservadas são normalizados para maiúsculas. As strings mantêm o
texto original.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import ply.lex as lex

from .errors import LexicalError


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
    "SUBROUTINE": "SUBROUTINE",
    "CALL": "CALL",
    "RETURN": "RETURN",
    "MOD": "MOD",
}


tokens = [
    "ID",
    "LABEL",
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
    "NEWLINE",
] + list(reserved.values())


# Tokens simples. O asterisco é usado em expressões e também em READ/PRINT *,
# cabendo ao parser decidir o significado em cada contexto.
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_ASSIGN = r"="
t_COMMA = r","
t_LPAREN = r"\("
t_RPAREN = r"\)"

# Espaços e tabs não separam instruções; a quebra de linha sim.
t_ignore = " \t\r"


def _line_start_index(text: str, position: int) -> int:
    """Devolve o índice do primeiro carácter da linha de ``position``."""

    previous_newline = text.rfind("\n", 0, position)
    return previous_newline + 1


def _is_at_statement_start(text: str, position: int) -> bool:
    """Indica se ``position`` está no início lógico de uma linha.

    Um número no início lógico da linha é tratado como ``LABEL``. Isto permite
    reconhecer instruções como ``10 CONTINUE`` sem confundir o ``10`` de
    ``DO 10 I = 1, N``.
    """

    start = _line_start_index(text, position)
    prefix = text[start:position]
    return prefix.strip() == ""


def _column(text: str, position: int) -> int:
    """Calcula a coluna humana, começando em 1."""

    return position - _line_start_index(text, position) + 1


def t_BOOL_LITERAL(t):
    r"\.(TRUE|FALSE)\."
    t.value = t.value.upper() == ".TRUE."
    return t


def t_LOGICAL_OP(t):
    r"\.(AND|OR)\."
    t.value = t.value[1:-1].upper()
    return t


def t_NOT_OP(t):
    r"\.NOT\."
    t.value = "NOT"
    return t


def t_REL_OP(t):
    r"\.(EQ|NE|LT|LE|GT|GE)\."
    t.value = t.value[1:-1].upper()
    return t


def t_REAL_LITERAL(t):
    r"(\d+\.\d*|\.\d+)([eE][+-]?\d+)?|\d+[eE][+-]?\d+"
    t.value = float(t.value)
    return t


def t_INTEGER_LITERAL(t):
    r"\d+"
    t.value = int(t.value)
    if _is_at_statement_start(t.lexer.lexdata, t.lexpos):
        t.type = "LABEL"
    return t


def t_STRING_LITERAL(t):
    r"'([^'\n]|'')*'"
    # Em Fortran, duas plicas consecutivas dentro da string representam uma
    # plica literal: 'It''s' -> It's.
    t.value = t.value[1:-1].replace("''", "'")
    return t


def t_ID(t):
    r"[A-Za-z_][A-Za-z0-9_]*"
    value = t.value.upper()
    t.type = reserved.get(value, "ID")
    t.value = value
    return t


def t_NEWLINE(t):
    r"\n+"
    t.lexer.lineno += len(t.value)
    t.value = "\n"
    return t


def t_error(t):
    column = _column(t.lexer.lexdata, t.lexpos)
    char = t.value[0]
    raise LexicalError(f"Carácter inesperado {char!r} na linha {t.lineno}, coluna {column}.")


def _remove_inline_comment(line: str) -> str:
    """Remove comentários iniciados por ! sem mexer em strings.

    O ponto de exclamação dentro de uma string não inicia comentário.
    """

    in_string = False
    i = 0
    while i < len(line):
        char = line[i]
        if char == "'":
            if in_string and i + 1 < len(line) and line[i + 1] == "'":
                i += 2
                continue
            in_string = not in_string
        elif char == "!" and not in_string:
            return line[:i]
        i += 1
    return line


def normalise_source(source: str) -> str:
    """Prepara o texto antes da tokenização.

    A normalização mantém a numeração de linhas e faz apenas transformações
    seguras para o subconjunto escolhido:

    - remove comentários iniciados por ``!``;
    - transforma ``END IF`` em ``ENDIF``, forma usada nos exemplos e no parser.

    Nesta versão não tratamos ``C``/``c`` na primeira coluna como comentário,
    porque o projeto assumiu formato livre e isso entraria em conflito com
    instruções válidas como ``CONTINUE`` ou identificadores começados por C.
    """

    normalised_lines: list[str] = []
    for raw_line in source.splitlines(keepends=True):
        newline = "\n" if raw_line.endswith("\n") else ""
        line = raw_line[:-1] if newline else raw_line

        line = _remove_inline_comment(line)
        line = re.sub(r"\bEND\s+IF\b", "ENDIF", line, flags=re.IGNORECASE)
        normalised_lines.append(line + newline)

    return "".join(normalised_lines)

def build_lexer(**kwargs):
    """Constrói e devolve um lexer PLY."""

    return lex.lex(reflags=re.IGNORECASE | re.VERBOSE, **kwargs)


@dataclass(frozen=True)
class TokenInfo:
    """Representação simples e estável de um token para testes e debug."""

    type: str
    value: object
    line: int
    column: int


def tokenize(source: str) -> list[TokenInfo]:
    """Tokeniza ``source`` e devolve uma lista de tokens independentes do PLY."""

    prepared_source = normalise_source(source)
    lexer = build_lexer()
    lexer.input(prepared_source)

    result: list[TokenInfo] = []
    while True:
        token = lexer.token()
        if token is None:
            break
        result.append(
            TokenInfo(
                type=token.type,
                value=token.value,
                line=token.lineno,
                column=_column(prepared_source, token.lexpos),
            )
        )
    return result


def format_tokens(tokens_to_format: Iterable[TokenInfo]) -> str:
    """Formata tokens numa tabela de texto para inspeção manual."""

    lines = ["TYPE                 VALUE                          LINE  COL"]
    lines.append("---------------------------------------------------------------")
    for token in tokens_to_format:
        value = repr(token.value)
        lines.append(f"{token.type:<20} {value:<30} {token.line:>4} {token.column:>4}")
    return "\n".join(lines) + "\n"
