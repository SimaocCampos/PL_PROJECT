"""Ponto de entrada do compilador Fortran 77 → EWVM."""

from __future__ import annotations

import argparse
from pathlib import Path


def compile_file(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")

    # Fase 0: apenas valida a leitura do ficheiro e prepara o output.
    message = (
        "Fase 0 concluída.\n"
        f"Ficheiro de entrada: {input_path}\n"
        f"Caracteres lidos: {len(source)}\n"
        "Próxima fase: implementar o lexer em src/lexer.py.\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(message, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compilador Fortran 77 → EWVM")
    parser.add_argument("input", help="Ficheiro Fortran de entrada (.f77)")
    parser.add_argument("-o", "--output", default="build/output.vm", help="Ficheiro VM de saída")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Erro: ficheiro não encontrado: {input_path}")

    compile_file(input_path, output_path)
    print(f"Fase 0 OK. Output escrito em: {output_path}")


if __name__ == "__main__":
    main()
