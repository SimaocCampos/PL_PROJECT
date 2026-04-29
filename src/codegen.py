"""Geração de código EWVM.

Este ficheiro será implementado na Fase 4.
"""


class LabelGenerator:
    def __init__(self):
        self._count = 0

    def new(self, prefix: str) -> str:
        label = f"{prefix}_{self._count}"
        self._count += 1
        return label


def generate(program) -> str:
    """Gera código EWVM a partir da AST validada.

    A implementação completa será feita na Fase 4.
    """
    raise NotImplementedError("Geração de código ainda não implementada. Fase prevista: Fase 4.")
