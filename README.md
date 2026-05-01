# Compilador Fortran 77 → EWVM

Projeto de Processamento de Linguagens 2026.

O objetivo é construir um compilador, em Python e com PLY, para um subconjunto de Fortran 77, gerando código para a máquina virtual EWVM.

## Estado atual

Fase 4 concluída:

- estrutura inicial do repositório;
- exemplos do enunciado em `tests/fortran/`;
- exemplos inválidos em `tests/invalid/`;
- lexer implementado com `ply.lex`;
- parser implementado com `ply.yacc`;
- construção de uma AST explícita em `src/ast_nodes.py`;
- análise semântica implementada em `src/semantic.py`;
- geração de código EWVM implementada em `src/codegen.py`;
- geração de VM para o programa principal com variáveis escalares, arrays unidimensionais, `READ`, `PRINT`, atribuições, expressões, `IF`, `GOTO` e `DO label ... CONTINUE`;
- modos de inspeção com `--tokens`, `--ast` e `--semantic`.

O exemplo 5 com `INTEGER FUNCTION` continua tratado como valorização para geração de código. A análise sintática e semântica já reconhece funções simples, mas a Fase 4 gera VM apenas para o programa principal e para as construções obrigatórias dos exemplos 1 a 4.

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
  decisoes.md      # Decisões técnicas

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

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --tokens
```

## Executar o parser

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --ast
```

## Executar a análise semântica

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --semantic
```

## Gerar código EWVM

Gerar um ficheiro VM:

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 -o build/exemplo_02_fatorial.vm
```

Gerar VM para os exemplos 1 a 4:

```bash
make vm-all
```

Os ficheiros de referência estão em:

```text
tests/expected_vm/
```

## Testes úteis

```bash
make smoke        # compila o hello world para VM
make ast-all      # gera AST dos exemplos
make semantic-all # gera relatórios semânticos
make vm-all       # gera VM dos exemplos 1 a 4
make invalid-all  # confirma erros semânticos esperados
```

## Objetivo do MVP

O primeiro objetivo é compilar corretamente estes exemplos:

1. `exemplo_01_hello.f77`
2. `exemplo_02_fatorial.f77`
3. `exemplo_03_primo.f77`
4. `exemplo_04_soma_array.f77`

O exemplo com `FUNCTION` é valorização. A próxima fase será estabilizar os exemplos 1 a 4 na EWVM real e, se sobrar tempo, atacar geração de código para `INTEGER FUNCTION`.
