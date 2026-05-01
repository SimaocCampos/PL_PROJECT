# Decisões técnicas

## 1. Formato de entrada

O compilador aceita uma forma livre de Fortran, semelhante aos exemplos do enunciado.

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

A geração de código não é feita diretamente nas regras do parser. O parser constrói uma AST. Esta decisão torna o código mais fácil de testar, explicar e defender.

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

## 4. Decisão lexical sobre labels

Os labels são reconhecidos lexicalmente quando um número inteiro aparece no início lógico de uma linha.

Exemplo:

```fortran
DO 10 I = 1, N
  FAT = FAT * I
10 CONTINUE
```

A primeira ocorrência de `10` é `INTEGER_LITERAL`; a segunda é `LABEL`.

## 5. Decisão sintática sobre `DO`

O parser reconhece `DO 10 I = 1, N` como uma instrução que referencia o label `10`, mas não transforma ainda o corpo do ciclo numa subárvore própria.

Isto segue a natureza label-based do Fortran 77. A análise semântica valida que o label existe, que aparece depois do `DO` e que corresponde a um `CONTINUE`.

## 6. Uso de nomes com argumentos

A sintaxe `NOME(ARG1, ARG2)` pode representar chamada de função ou acesso indexado, dependendo do contexto semântico. O parser guarda esta forma como `NameUse` com argumentos.

A análise semântica decide:

- se o nome existir como função conhecida, trata-se de uma chamada de função;
- se o nome existir como array, trata-se de um acesso indexado;
- se o nome for escalar, o uso com argumentos é erro semântico.

A função intrínseca `MOD(...)` é guardada diretamente como `FunctionCall`, porque é palavra reservada no lexer.

## 7. Regras semânticas atuais

A Fase 3 valida:

- duplicação de símbolos no mesmo âmbito;
- uso de nomes não declarados;
- uso correto de escalares e arrays;
- tipos de expressões aritméticas, relacionais e lógicas;
- compatibilidade de tipos em atribuições;
- condição lógica em `IF`;
- variável de controlo inteira em `DO`;
- labels existentes em `GOTO`;
- correspondência entre `DO label` e `label CONTINUE`;
- uso de `RETURN` apenas em funções;
- parâmetros declarados nas funções;
- chamadas simples a funções definidas pelo utilizador.

## 8. Valorização

Só depois do MVP estar funcional serão considerados:

- geração de código completa para `INTEGER FUNCTION`;
- `SUBROUTINE`;
- otimizações simples.

A chamada de funções já é validada semanticamente em casos simples, mas a geração de VM para funções fica para depois dos exemplos 1 a 4 estarem estáveis.

## 9. Reaproveitamento do projeto antigo

O projeto antigo serve como referência de organização e de geração EWVM, mas não como base gramatical, porque era Pascal e este projeto é Fortran 77.
