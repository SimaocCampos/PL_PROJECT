# Compilador Fortran 77 para EWVM

## 1. Introdução

Este relatório descreve a implementação de um compilador para um subconjunto da linguagem Fortran 77, desenvolvido no contexto da unidade curricular de Processamento de Linguagens.

O compilador recebe programas Fortran como entrada e produz código para a máquina virtual EWVM.

## 2. Objetivos e âmbito

O objetivo principal é suportar as construções essenciais indicadas no enunciado:

- declarações de variáveis;
- expressões aritméticas, relacionais e lógicas;
- instruções de input/output;
- estruturas condicionais;
- ciclos `DO` com labels;
- saltos com `GOTO`;
- geração de código VM.

## 3. Decisões de implementação

### 3.1 Formato Fortran suportado

Foi decidido suportar uma forma livre de Fortran, mantendo labels numéricos e a sintaxe dos exemplos fornecidos.

### 3.2 Arquitetura

A implementação foi dividida nos seguintes módulos:

- `lexer.py`;
- `parser.py`;
- `ast_nodes.py`;
- `semantic.py`;
- `codegen.py`;
- `compiler.py`.

A pipeline usada é:

```text
código fonte → tokens → AST → AST validada → código EWVM
```

## 4. Análise léxica

A preencher na Fase 1.

## 5. Análise sintática

A preencher na Fase 2.

## 6. Análise semântica

A preencher na Fase 3.

## 7. Geração de código

A preencher na Fase 4.

## 8. Testes

Os exemplos de teste encontram-se em `tests/fortran/` e `tests/invalid/`.

## 9. Dificuldades encontradas

A preencher durante o desenvolvimento.

## 10. Como executar

```bash
python -m src.compiler tests/fortran/exemplo_01_hello.f77 -o build/exemplo_01_hello.vm
```
