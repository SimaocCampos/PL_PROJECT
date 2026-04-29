"""Ponto de entrada do compilador Fortran 77 → EWVM."""

from __future__ import annotations

import argparse
from pathlib import Path

from .ast_nodes import format_ast
from .lexer import format_tokens, tokenize
from .parser import parse


def compile_file(input_path: Path, output_path: Path) -> None:
    """Executa a pipeline disponível do compilador.

    Na Fase 2 já existem análise léxica, análise sintática e construção da
    AST. A análise semântica e a geração de VM serão implementadas nas fases
    seguintes, por isso o ficheiro de saída ainda é informativo.
    """

    source = input_path.read_text(encoding="utf-8")
    ast = parse(source)

    message = (
        "Fase 2 concluída: análise léxica e sintática executadas com sucesso.\n"
        f"Ficheiro de entrada: {input_path}\n"
        f"Programa reconhecido: {ast.program.name}\n"
        f"Subprogramas reconhecidos: {len(ast.subprograms)}\n"
        "A análise semântica será implementada na Fase 3.\n"
        "A geração de código VM será implementada na Fase 4.\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(message, encoding="utf-8")


def write_tokens(input_path: Path, output_path: Path | None = None) -> None:
    """Tokeniza um ficheiro e imprime ou escreve a tabela de tokens."""

    source = input_path.read_text(encoding="utf-8")
    text = format_tokens(tokenize(source))
    _write_or_print(text, output_path, "Tokens")


def write_ast(input_path: Path, output_path: Path | None = None) -> None:
    """Faz parse de um ficheiro e imprime ou escreve a AST."""

    source = input_path.read_text(encoding="utf-8")
    text = format_ast(parse(source))
    _write_or_print(text, output_path, "AST")


def _write_or_print(text: str, output_path: Path | None, label: str) -> None:
    if output_path is None:
        print(text, end="")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"{label} escrita em: {output_path}")


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
    parser.add_argument(
        "--ast",
        action="store_true",
        help="Mostra a AST construída pelo parser em formato JSON",
    )
    parser.add_argument(
        "--ast-output",
        help="Escreve a AST em formato JSON para o ficheiro indicado",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    tokens_output_path = Path(args.tokens_output) if args.tokens_output else None
    ast_output_path = Path(args.ast_output) if args.ast_output else None

    if not input_path.exists():
        raise SystemExit(f"Erro: ficheiro não encontrado: {input_path}")

    if args.tokens or tokens_output_path is not None:
        write_tokens(input_path, tokens_output_path)
        return

    if args.ast or ast_output_path is not None:
        write_ast(input_path, ast_output_path)
        return

    compile_file(input_path, output_path)
    print(f"Fase 2 OK. Output escrito em: {output_path}")


if __name__ == "__main__":
    main()
