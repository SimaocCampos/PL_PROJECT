# Compilador Fortran 77 → EWVM

Projeto de Processamento de Linguagens 2026.

O objetivo é construir um compilador, em Python e com PLY, para um subconjunto de Fortran 77, gerando código para a máquina virtual EWVM.

## Estado atual

Fase 2 concluída:

- estrutura inicial do repositório;
- exemplos do enunciado em `tests/fortran/`;
- exemplos inválidos iniciais em `tests/invalid/`;
- lexer implementado com `ply.lex`;
- parser implementado com `ply.yacc`;
- construção de uma AST explícita em `src/ast_nodes.py`;
- suporte sintático para declarações, atribuições, `READ`, `PRINT`, `IF/ELSE/ENDIF`, `DO`, `CONTINUE`, `GOTO`, `RETURN` e `INTEGER/REAL/LOGICAL FUNCTION`;
- modos de inspeção com `--tokens` e `--ast`.

A próxima fase é a implementação da análise semântica em `src/semantic.py`.

## Decisão sobre o formato Fortran

Este projeto suporta uma forma livre inspirada nos exemplos do enunciado, em vez do formato rígido de colunas fixas do Fortran 77.

Continuam a ser suportados labels numéricos, por exemplo:

```fortran
DO 10 I = 1, N
  FAT = FAT * I
10 CONTINUE
```

Neste caso, o `10` após `DO` é um inteiro normal e o `10` no início da linha é reconhecido como `LABEL`.

## Estrutura

```text
src/
  compiler.py      # Ponto de entrada do compilador
  lexer.py         # Analisador léxico com PLY
  parser.py        # Analisador sintático com PLY
  ast_nodes.py     # Nós da AST
  semantic.py      # Análise semântica e tabela de símbolos
  codegen.py       # Geração de código EWVM
  errors.py        # Exceções e mensagens de erro

tests/
  fortran/         # Programas Fortran válidos
  invalid/         # Programas Fortran inválidos
  expected_vm/     # Código VM esperado/validado

docs/
  decisoes.md      # Decisões técnicas iniciais

relatorio.md       # Relatório técnico
requirements.txt   # Dependências Python
```

## Preparação do ambiente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar o lexer

Mostrar tokens no terminal:

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --tokens
```

Guardar tokens num ficheiro:

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --tokens-output build/exemplo_02_fatorial.tokens
```

## Executar o parser

Mostrar a AST no terminal:

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --ast
```

Guardar a AST num ficheiro JSON:

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --ast-output build/exemplo_02_fatorial.ast.json
```

Testar a construção de AST para os exemplos válidos:

```bash
make ast-all
```

## Smoke test desta fase

```bash
make smoke
```

O comando normal ainda não gera VM real. Apenas confirma que a análise léxica e sintática correram com sucesso:

```bash
python -m src.compiler tests/fortran/exemplo_01_hello.f77 -o build/exemplo_01_hello.vm
```

## Objetivo do MVP

O primeiro objetivo é compilar corretamente estes exemplos:

1. `exemplo_01_hello.f77`
2. `exemplo_02_fatorial.f77`
3. `exemplo_03_primo.f77`
4. `exemplo_04_soma_array.f77`

O exemplo com `FUNCTION` já é aceite sintaticamente, mas a validação semântica e a geração de código para funções continuam a ser valorização.
