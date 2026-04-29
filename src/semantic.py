"""Análise semântica e tabela de símbolos.

Este ficheiro será implementado na Fase 3.
"""

from dataclasses import dataclass


@dataclass
class Symbol:
    name: str
    type_name: str
    position: int
    size: int = 1


class SymbolTable:
    def __init__(self):
        self._symbols: dict[str, Symbol] = {}

    def add(self, symbol: Symbol) -> None:
        if symbol.name in self._symbols:
            raise ValueError(f"Símbolo já declarado: {symbol.name}")
        self._symbols[symbol.name] = symbol

    def get(self, name: str) -> Symbol:
        return self._symbols[name]


def analyse(program):
    """Valida semanticamente a AST.

    A implementação completa será feita na Fase 3.
    """
    raise NotImplementedError("Análise semântica ainda não implementada. Fase prevista: Fase 3.")
