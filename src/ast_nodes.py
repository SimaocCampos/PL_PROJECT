"""Nós da árvore sintática abstrata do compilador Fortran 77.

O parser constrói estas estruturas e as fases seguintes usam-nas para
validação semântica e geração de código. Os nós são simples ``dataclasses``
para serem fáceis de inspecionar durante a defesa.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any
import json


@dataclass
class ProgramFile:
    """Ficheiro Fortran reconhecido pelo compilador."""

    program: Program
    subprograms: list[Function]


@dataclass
class Program:
    """Programa principal."""

    name: str
    declarations: list[Declaration]
    statements: list[Statement]


@dataclass
class Function:
    """Função Fortran simples, usada como valorização sintática inicial."""

    name: str
    return_type: str
    parameters: list[str]
    declarations: list[Declaration]
    statements: list[Statement]


@dataclass
class Declaration:
    """Declaração de uma ou mais variáveis do mesmo tipo."""

    type_name: str
    variables: list[VariableDeclaration]


@dataclass
class VariableDeclaration:
    """Variável declarada, opcionalmente com dimensões de array."""

    name: str
    dimensions: list[Expression]


class Statement:
    """Classe base apenas documental para instruções da AST."""


@dataclass
class LabelledStatement(Statement):
    """Instrução precedida por um label numérico."""

    label: int
    statement: Statement


@dataclass
class Assignment(Statement):
    """Atribuição ``alvo = expressão``."""

    target: NameUse
    expression: Expression


@dataclass
class Read(Statement):
    """Instrução ``READ *, ...``."""

    items: list[NameUse]


@dataclass
class Print(Statement):
    """Instrução ``PRINT *, ...``."""

    items: list[Expression]


@dataclass
class If(Statement):
    """Bloco ``IF (...) THEN ... ELSE ... ENDIF``."""

    condition: Expression
    then_statements: list[Statement]
    else_statements: list[Statement]


@dataclass
class Do(Statement):
    """Instrução ``DO label var = início, fim[, passo]``.

    No Fortran 77 o corpo termina no ``CONTINUE`` com o label indicado. Nesta
    fase guardamos a instrução como referência ao label; a validação da
    correspondência fica para a análise semântica.
    """

    end_label: int
    variable: str
    start: Expression
    end: Expression
    step: Expression | None


@dataclass
class Goto(Statement):
    """Salto incondicional para um label."""

    label: int


@dataclass
class Continue(Statement):
    """Instrução ``CONTINUE``."""


@dataclass
class Return(Statement):
    """Instrução ``RETURN``."""


class Expression:
    """Classe base apenas documental para expressões da AST."""


@dataclass
class Literal(Expression):
    """Literal inteiro, real, lógico ou string."""

    value: Any
    type_name: str


@dataclass
class NameUse(Expression):
    """Uso de um nome, com argumentos/índices opcionais.

    ``A`` fica com ``arguments=[]``. ``A(I)`` e ``F(X,Y)`` ficam ambos com
    argumentos; a análise semântica decide se o nome é array ou função.
    """

    name: str
    arguments: list[Expression]


@dataclass
class UnaryOp(Expression):
    """Operador unário."""

    operator: str
    operand: Expression


@dataclass
class BinaryOp(Expression):
    """Operador binário."""

    operator: str
    left: Expression
    right: Expression


@dataclass
class FunctionCall(Expression):
    """Chamada a função intrínseca/reservada, como ``MOD``."""

    name: str
    arguments: list[Expression]


def ast_to_dict(node: Any) -> Any:
    """Converte a AST para estruturas Python serializáveis em JSON."""

    if is_dataclass(node):
        data = {"node": node.__class__.__name__}
        for field in fields(node):
            data[field.name] = ast_to_dict(getattr(node, field.name))
        return data
    if isinstance(node, list):
        return [ast_to_dict(item) for item in node]
    if isinstance(node, tuple):
        return [ast_to_dict(item) for item in node]
    return node


def format_ast(node: Any) -> str:
    """Devolve uma representação JSON indentada da AST."""

    return json.dumps(ast_to_dict(node), indent=2, ensure_ascii=False) + "\n"
