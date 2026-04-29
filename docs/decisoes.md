# Decisões técnicas iniciais

## 1. Formato de entrada

O compilador vai aceitar uma forma livre de Fortran, semelhante aos exemplos do enunciado.

Não serão implementadas, na primeira versão, as regras de colunas fixas do Fortran 77 clássico.

Motivo: a escolha reduz a complexidade do lexer e permite concentrar o trabalho nas fases principais do compilador: análise léxica, análise sintática, análise semântica e geração de código EWVM.

## 2. Pipeline

A pipeline será:

```text
ficheiro .f77
  → lexer
  → parser
  → AST
  → análise semântica
  → geração EWVM
  → ficheiro .vm
```

A geração de código não será feita diretamente nas regras do parser. O parser deve construir uma AST. Esta decisão torna o código mais fácil de testar, explicar e defender.

## 3. Subconjunto inicial da linguagem

O MVP deve suportar:

- `PROGRAM ... END`;
- `INTEGER`, `REAL`, `LOGICAL`;
- variáveis escalares;
- arrays unidimensionais simples;
- atribuições;
- expressões aritméticas;
- expressões relacionais e lógicas;
- `IF (...) THEN ... ELSE ... ENDIF`;
- `DO label var = inicio, fim`;
- labels numéricos;
- `CONTINUE`;
- `GOTO`;
- `READ *, var`;
- `PRINT *, ...`;
- função intrínseca `MOD(a, b)`.

## 4. Valorização

Só depois do MVP estar funcional serão considerados:

- `INTEGER FUNCTION`;
- `RETURN`;
- chamada de funções definidas pelo utilizador;
- `SUBROUTINE`;
- otimizações simples.

## 5. Reaproveitamento do projeto antigo

O projeto antigo serve como referência de organização e de geração EWVM, mas não como base gramatical, porque era Pascal e este projeto é Fortran 77.
