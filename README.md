# Compilador Fortran 77 → EWVM

Projeto de Processamento de Linguagens 2026.

O objetivo é construir um compilador, em Python e com PLY, para um subconjunto de Fortran 77, gerando código para a máquina virtual EWVM.

## Estado atual

Fase 0 concluída:

- estrutura inicial do repositório;
- exemplos do enunciado em `tests/fortran/`;
- exemplos inválidos iniciais em `tests/invalid/`;
- esqueleto dos módulos do compilador;
- esqueleto do relatório técnico;
- decisões iniciais documentadas em `docs/decisoes.md`.

A próxima fase é a implementação do analisador léxico em `src/lexer.py`.

## Decisão sobre o formato Fortran

Este projeto vai suportar uma forma livre inspirada nos exemplos do enunciado, em vez do formato rígido de colunas fixas do Fortran 77.

Continuam a ser suportados labels numéricos, por exemplo:

```fortran
DO 10 I = 1, N
  FAT = FAT * I
10 CONTINUE
```

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

## Execução nesta fase

Nesta fase, o comando apenas confirma que o ficheiro é lido corretamente e mostra o estado da pipeline.

```bash
python -m src.compiler tests/fortran/exemplo_01_hello.f77 -o build/exemplo_01_hello.vm
```

## Objetivo do MVP

O primeiro objetivo é compilar corretamente estes exemplos:

1. `exemplo_01_hello.f77`
2. `exemplo_02_fatorial.f77`
3. `exemplo_03_primo.f77`
4. `exemplo_04_soma_array.f77`

O exemplo com `FUNCTION` fica como valorização.
