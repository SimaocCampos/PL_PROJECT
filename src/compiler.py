"""Ponto de entrada do compilador Fortran 77 → EWVM."""

from __future__ import annotations

import argparse
from pathlib import Path

from .lexer import format_tokens, tokenize


def compile_file(input_path: Path, output_path: Path) -> None:
    """Executa a pipeline completa do compilador.

    Nesta fase ainda só existe análise léxica. A função mantém o comando da
    Fase 0 funcional e escreve um ficheiro informativo para não fingir que já
    existe geração de VM.
    """

    source = input_path.read_text(encoding="utf-8")
    tokens = tokenize(source)

    message = (
        "Fase 1 concluída: análise léxica executada com sucesso.\n"
        f"Ficheiro de entrada: {input_path}\n"
        f"Tokens reconhecidos: {len(tokens)}\n"
        "A geração de código VM será implementada na Fase 4.\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(message, encoding="utf-8")


def write_tokens(input_path: Path, output_path: Path | None = None) -> None:
    """Tokeniza um ficheiro e imprime ou escreve a tabela de tokens."""

    source = input_path.read_text(encoding="utf-8")
    text = format_tokens(tokenize(source))

    if output_path is None:
        print(text, end="")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"Tokens escritos em: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compilador Fortran 77 → EWVM")
    parser.add_argument("input", help="Ficheiro Fortran de entrada (.f77)")
    parser.add_argument("-o", "--output", default="build/output.vm", help="Ficheiro VM de saída")
    parser.add_argument(
        "--tokens",
        action="store_true",
        help="Mostra a sequência de tokens reconhecida pelo lexer",
    )
    parser.add_argument(
        "--tokens-output",
        help="Escreve a sequência de tokens para o ficheiro indicado",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    tokens_output_path = Path(args.tokens_output) if args.tokens_output else None

    if not input_path.exists():
        raise SystemExit(f"Erro: ficheiro não encontrado: {input_path}")

    if args.tokens or tokens_output_path is not None:
        write_tokens(input_path, tokens_output_path)
        return

    compile_file(input_path, output_path)
    print(f"Fase 1 OK. Output escrito em: {output_path}")


if __name__ == "__main__":
    main()
