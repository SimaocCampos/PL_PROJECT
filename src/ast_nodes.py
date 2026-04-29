"""Nós da árvore sintática abstrata.

A AST será preenchida na Fase 2. O objetivo deste ficheiro é concentrar
as estruturas de dados produzidas pelo parser e consumidas pela análise
semântica e pela geração de código.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Program:
    name: str
    declarations: list[Any]
    statements: list[Any]
