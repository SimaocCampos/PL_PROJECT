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

Foi decidido suportar uma forma livre de Fortran, mantendo labels numéricos e a sintaxe dos exemplos fornecidos. Assim, não são implementadas as regras clássicas de colunas fixas do Fortran 77 nesta primeira versão.

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

A análise léxica foi implementada com `ply.lex` no ficheiro `src/lexer.py`.

O lexer reconhece:

- palavras reservadas: `PROGRAM`, `END`, `INTEGER`, `REAL`, `LOGICAL`, `IF`, `THEN`, `ELSE`, `ENDIF`, `DO`, `CONTINUE`, `GOTO`, `READ`, `PRINT`, `FUNCTION`, `RETURN`, entre outras;
- identificadores, normalizados para maiúsculas, porque Fortran não distingue maiúsculas de minúsculas;
- literais inteiros e reais;
- literais lógicos `.TRUE.` e `.FALSE.`;
- strings delimitadas por plicas;
- operadores aritméticos: `+`, `-`, `*`, `/`;
- operadores relacionais: `.EQ.`, `.NE.`, `.LT.`, `.LE.`, `.GT.`, `.GE.`;
- operadores lógicos: `.AND.`, `.OR.`, `.NOT.`;
- labels numéricos no início lógico de uma linha;
- quebras de linha, usadas mais tarde pelo parser para separar instruções.

Os comentários iniciados por `!` são removidos antes da tokenização, exceto quando o símbolo aparece dentro de uma string. Como o projeto assume formato livre, `C`/`c` na primeira coluna não é tratado como comentário, para não criar conflitos com instruções válidas como `CONTINUE`.

Para efeitos de teste, o compilador disponibiliza o modo:

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --tokens
```

## 5. Análise sintática

A análise sintática foi implementada com `ply.yacc` no ficheiro `src/parser.py`.

O parser recebe os tokens produzidos pelo lexer e constrói uma árvore sintática abstrata definida em `src/ast_nodes.py`. A geração de código não é feita diretamente nas regras sintáticas, para manter a separação entre parsing, validação semântica e geração de VM.

### 5.1 Estrutura geral reconhecida

A estrutura principal reconhecida é:

```text
source
  → program_unit function_unit*

program_unit
  → PROGRAM ID declarations statements END

function_unit
  → type FUNCTION ID '(' parameters ')' declarations statements END
```

As funções são reconhecidas para permitir analisar o exemplo de valorização.

### 5.2 Declarações

As declarações reconhecidas seguem o padrão:

```text
declaration_line
  → type declarator_list

type
  → INTEGER | REAL | LOGICAL

declarator
  → ID
  | ID '(' argument_list ')'
```

Isto permite reconhecer variáveis escalares e arrays simples, como:

```fortran
INTEGER N, I, FAT
INTEGER NUMS(5)
```

### 5.3 Instruções

O parser reconhece as seguintes instruções:

- atribuição: `X = expr`;
- leitura: `READ *, X`;
- escrita: `PRINT *, ...`;
- condicional: `IF (...) THEN ... ELSE ... ENDIF`;
- ciclo label-based: `DO 10 I = 1, N`;
- salto: `GOTO 20`;
- `CONTINUE`;
- `RETURN`.

Os labels são representados por nós `LabelledStatement`. Por exemplo:

```fortran
20 IF (I .LE. N) THEN
```

é representado como uma instrução `If` associada ao label `20`.

### 5.4 Expressões

As expressões suportam:

- literais inteiros, reais, lógicos e strings;
- nomes simples;
- nomes com argumentos/índices;
- operadores aritméticos `+`, `-`, `*`, `/`;
- operadores relacionais `.EQ.`, `.NE.`, `.LT.`, `.LE.`, `.GT.`, `.GE.`;
- operadores lógicos `.AND.`, `.OR.`, `.NOT.`;
- parênteses;
- chamada da função intrínseca `MOD(...)`.

A precedência definida no parser coloca operadores lógicos abaixo dos relacionais, e estes abaixo dos aritméticos.

Para efeitos de teste, o compilador disponibiliza o modo:

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --ast
```

## 6. Análise semântica

A análise semântica foi implementada em `src/semantic.py` e segue a abordagem apresentada nas aulas: a AST é percorrida depois da análise sintática e é validada com apoio de tabelas de símbolos.

Cada unidade Fortran tem uma tabela de símbolos própria:

- uma tabela para o programa principal;
- uma tabela para cada função;
- uma tabela de assinaturas de funções, partilhada pelo ficheiro.

A tabela de símbolos guarda, para cada nome:

- nome normalizado;
- tipo (`INTEGER`, `REAL` ou `LOGICAL`);
- posição futura para geração de código;
- tamanho ocupado;
- dimensões, quando se trata de array;
- categoria (`variable`, `function` ou `return`).

A análise semântica valida:

- declaração duplicada de variáveis;
- uso de nomes não declarados;
- uso de arrays sem índice;
- uso de escalares com índices;
- número e tipo dos índices de arrays;
- compatibilidade de tipos em atribuições;
- tipos de operandos em expressões aritméticas, relacionais e lógicas;
- condição de `IF` com tipo `LOGICAL`;
- variável de controlo de `DO` escalar e `INTEGER`;
- limites de `DO` com tipo `INTEGER`;
- existência de labels usados em `GOTO`;
- existência e posição posterior do label usado em `DO`;
- correspondência entre `DO label` e `label CONTINUE`;
- uso de `RETURN` apenas dentro de funções;
- parâmetros declarados nas funções;
- chamadas a funções definidas pelo utilizador com número de argumentos correto;
- chamada à função intrínseca `MOD` com dois argumentos inteiros.

O modo de inspeção semântica é:

```bash
python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --semantic
```

Também é possível gerar relatórios JSON para todos os exemplos válidos:

```bash
make semantic-all
```

## 7. Geração de código

A preencher na Fase 4.

## 8. Testes

Os exemplos de teste encontram-se em `tests/fortran/` e `tests/invalid/`.

Nesta fase, os exemplos válidos do enunciado são usados para confirmar que o lexer reconhece tokens, o parser constrói a AST e a análise semântica valida corretamente o programa. O comando `make semantic-all` gera ficheiros JSON com as tabelas de símbolos e labels reconhecidos.

Foram também adicionados testes inválidos para verificar erros como:

- variável usada sem declaração;
- atribuição com tipo incompatível;
- label inexistente em `DO`;
- variável declarada duas vezes;
- índice de array com tipo lógico;
- label de `DO` que não corresponde a `CONTINUE`;
- `RETURN` fora de função.

Esses testes podem ser executados com:

```bash
make invalid-all
```

## 9. Dificuldades encontradas

Uma dificuldade inicial foi distinguir números inteiros normais de labels. A solução adotada foi classificar como `LABEL` apenas números que aparecem no início lógico de uma linha. Assim, em `DO 10 I = 1, N`, o `10` é um inteiro literal; em `10 CONTINUE`, o `10` é um label.

Outra dificuldade foi a ambiguidade entre acesso a arrays e chamada de funções, já que ambas usam a forma `NOME(...)`. A solução adotada foi guardar a construção no parser como `NameUse` com argumentos e decidir na análise semântica: se o nome corresponder a uma função conhecida, é chamada de função; se corresponder a um array, é acesso indexado.

A terceira dificuldade foi representar ciclos `DO` de Fortran 77. Nesta fase, o parser guarda o `DO` como instrução com referência ao label final. A análise semântica valida se esse label existe, se aparece depois do `DO` e se está associado a uma instrução `CONTINUE`.

## 10. Como executar

```bash
python -m src.compiler tests/fortran/exemplo_01_hello.f77 --tokens
python -m src.compiler tests/fortran/exemplo_01_hello.f77 --ast
python -m src.compiler tests/fortran/exemplo_01_hello.f77 --semantic
python -m src.compiler tests/fortran/exemplo_01_hello.f77 -o build/exemplo_01_hello.vm
```
