"""Geração de código EWVM para o subconjunto de Fortran 77.

Esta fase recebe uma AST já validada semanticamente e o relatório semântico
com as posições das variáveis. A geração é feita para uma máquina virtual de
pilha, usando o padrão trabalhado nas aulas: reservar variáveis globais com
``PUSHI``/``PUSHF``, avaliar expressões deixando o valor no topo da pilha,
usar ``STOREG``/``PUSHG`` para variáveis e ``JZ``/``JUMP`` para controlo de
fluxo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .ast_nodes import (
    Assignment,
    BinaryOp,
    Continue,
    Do,
    FunctionCall,
    Goto,
    If,
    LabelledStatement,
    Literal,
    NameUse,
    Print,
    ProgramFile,
    Read,
    Return,
    UnaryOp,
)
from .errors import CodeGenerationError
from .semantic import INTEGER, LOGICAL, REAL, STRING, SemanticReport, Symbol, UnitReport


class LabelGenerator:
    """Gerador simples de labels internos, garantindo nomes únicos."""

    def __init__(self) -> None:
        self._count = 0

    def new(self, prefix: str) -> str:
        label = f"{prefix}_{self._count}"
        self._count += 1
        return label


@dataclass
class UnitContext:
    """Contexto necessário para gerar código de uma unidade Fortran."""

    name: str
    symbols: dict[str, Symbol]
    label_generator: LabelGenerator

    def symbol(self, name: str) -> Symbol:
        key = name.upper()
        if key not in self.symbols:
            raise CodeGenerationError(
                f"Símbolo {key!r} não encontrado durante a geração de código. "
                "A análise semântica deveria ter detetado este problema."
            )
        return self.symbols[key]


class CodeGenerator:
    """Gerador de código EWVM para o programa principal."""

    def __init__(self, ast: ProgramFile, semantic_report: SemanticReport):
        self.ast = ast
        self.semantic_report = semantic_report
        self.labels = LabelGenerator()

    def generate(self) -> str:
        """Gera o programa EWVM completo."""

        if self.ast.subprograms:
            # A análise sintática/semântica já aceita funções como valorização,
            # mas a geração de chamadas reais fica separada do MVP. O exemplo 5
            # continua documentado como trabalho de valorização.
            raise CodeGenerationError(
                "A Fase 4 gera código para o programa principal e para as "
                "construções obrigatórias. FUNCTION/SUBROUTINE ficam para valorização."
            )

        context = self._context_from_report(self.semantic_report.main)
        instructions: list[str] = []
        instructions.extend(self._emit_global_initialisation(context))
        instructions.append("start")
        instructions.extend(self._emit_statements(self.ast.program.statements, context))
        instructions.append("stop")
        return self._format(instructions)

    def _context_from_report(self, report: UnitReport) -> UnitContext:
        symbols = {symbol.name.upper(): symbol for symbol in report.symbols}
        return UnitContext(
            name=report.name,
            symbols=symbols,
            label_generator=self.labels,
        )

    def _emit_global_initialisation(self, context: UnitContext) -> list[str]:
        instructions: list[str] = []
        for symbol in sorted(context.symbols.values(), key=lambda entry: entry.position):
            if symbol.kind == "function":
                # No programa principal, uma função declarada como INTEGER F serve
                # para permitir chamadas. Não é uma variável local a reservar.
                continue
            instructions.extend(self._default_value(symbol.type_name) for _ in range(symbol.size))
        return instructions

    def _default_value(self, type_name: str) -> str:
        if type_name in {INTEGER, LOGICAL}:
            return "pushi 0"
        if type_name == REAL:
            return "pushf 0.0"
        if type_name == STRING:
            return 'pushs ""'
        raise CodeGenerationError(f"Tipo sem valor inicial EWVM conhecido: {type_name}.")

    def _emit_statements(self, statements: list[object], context: UnitContext) -> list[str]:
        instructions: list[str] = []
        index = 0

        while index < len(statements):
            statement = statements[index]
            real_statement = self._unwrap(statement)

            if isinstance(real_statement, Do):
                end_index = self._find_matching_continue(statements, index, real_statement.end_label)
                body = statements[index + 1 : end_index]
                instructions.extend(self._emit_do(real_statement, body, context))
                index = end_index + 1
                continue

            instructions.extend(self._emit_statement_with_optional_label(statement, context))
            index += 1

        return instructions

    def _emit_statement_with_optional_label(self, statement: object, context: UnitContext) -> list[str]:
        instructions: list[str] = []
        real_statement = statement

        if isinstance(statement, LabelledStatement):
            instructions.append(self._source_label(statement.label))
            real_statement = statement.statement

        instructions.extend(self._emit_statement(real_statement, context))
        return instructions

    def _emit_statement(self, statement: object, context: UnitContext) -> list[str]:
        if isinstance(statement, Assignment):
            return self._emit_assignment(statement, context)

        if isinstance(statement, Read):
            return self._emit_read(statement, context)

        if isinstance(statement, Print):
            return self._emit_print(statement, context)

        if isinstance(statement, If):
            return self._emit_if(statement, context)

        if isinstance(statement, Do):
            raise CodeGenerationError(
                f"DO com label {statement.end_label} não foi agrupado corretamente."
            )

        if isinstance(statement, Goto):
            return [f"jump {self._source_label_name(statement.label)}"]

        if isinstance(statement, Continue):
            return []

        if isinstance(statement, Return):
            raise CodeGenerationError("RETURN só é suportado quando a geração de FUNCTION for ativada.")

        raise CodeGenerationError(f"Instrução sem geração de código: {statement!r}.")

    def _emit_assignment(self, statement: Assignment, context: UnitContext) -> list[str]:
        symbol = context.symbol(statement.target.name)

        value_code = self._emit_expression_with_conversion(
            statement.expression, context, expected_type=symbol.type_name
        )
        if statement.target.arguments:
            return self._emit_array_address(statement.target, context) + value_code + ["storen"]

        return value_code + [f"storeg {symbol.position}"]

    def _emit_read(self, statement: Read, context: UnitContext) -> list[str]:
        instructions: list[str] = []
        for item in statement.items:
            symbol = context.symbol(item.name)
            if item.arguments:
                instructions.extend(self._emit_array_address(item, context))
                instructions.extend(self._emit_read_value(symbol.type_name))
                instructions.append("storen")
            else:
                instructions.extend(self._emit_read_value(symbol.type_name))
                instructions.append(f"storeg {symbol.position}")
        return instructions

    def _emit_read_value(self, type_name: str) -> list[str]:
        if type_name in {INTEGER, LOGICAL}:
            return ["read", "atoi"]
        if type_name == REAL:
            return ["read", "atof"]
        if type_name == STRING:
            return ["read"]
        raise CodeGenerationError(f"Tipo sem leitura EWVM conhecida: {type_name}.")

    def _emit_print(self, statement: Print, context: UnitContext) -> list[str]:
        instructions: list[str] = []
        for item in statement.items:
            item_type = self._infer_expression_type(item, context)
            instructions.extend(self._emit_expression(item, context))
            instructions.append(self._write_instruction(item_type))
        instructions.append("writeln")
        return instructions

    def _write_instruction(self, type_name: str) -> str:
        if type_name in {INTEGER, LOGICAL}:
            return "writei"
        if type_name == REAL:
            return "writef"
        if type_name == STRING:
            return "writes"
        raise CodeGenerationError(f"Tipo sem instrução de escrita EWVM conhecida: {type_name}.")

    def _emit_if(self, statement: If, context: UnitContext) -> list[str]:
        instructions = self._emit_expression(statement.condition, context)

        if statement.else_statements:
            else_label = context.label_generator.new("IF_ELSE")
            end_label = context.label_generator.new("IF_END")
            instructions.append(f"jz {else_label}")
            instructions.extend(self._emit_statements(statement.then_statements, context))
            instructions.append(f"jump {end_label}")
            instructions.append(f"{else_label}:")
            instructions.extend(self._emit_statements(statement.else_statements, context))
            instructions.append(f"{end_label}:")
            return instructions

        end_label = context.label_generator.new("IF_END")
        instructions.append(f"jz {end_label}")
        instructions.extend(self._emit_statements(statement.then_statements, context))
        instructions.append(f"{end_label}:")
        return instructions

    def _emit_do(self, statement: Do, body: list[object], context: UnitContext) -> list[str]:
        variable = context.symbol(statement.variable)
        start_label = context.label_generator.new(f"DO_{statement.end_label}_START")
        end_label = context.label_generator.new(f"DO_{statement.end_label}_END")
        step_expression = statement.step if statement.step is not None else Literal(1, INTEGER)

        instructions: list[str] = []
        instructions.extend(self._emit_expression(statement.start, context))
        instructions.append(f"storeg {variable.position}")
        instructions.append(f"{start_label}:")
        instructions.append(f"pushg {variable.position}")
        instructions.extend(self._emit_expression(statement.end, context))
        instructions.append("infeq")
        instructions.append(f"jz {end_label}")
        instructions.extend(self._emit_statements(body, context))
        # O label fonte fica antes do incremento, correspondendo ao CONTINUE do Fortran.
        instructions.append(self._source_label(statement.end_label))
        instructions.append(f"pushg {variable.position}")
        instructions.extend(self._emit_expression(step_expression, context))
        instructions.append("add")
        instructions.append(f"storeg {variable.position}")
        instructions.append(f"jump {start_label}")
        instructions.append(f"{end_label}:")
        return instructions

    def _emit_expression(self, expression: object, context: UnitContext) -> list[str]:
        if isinstance(expression, Literal):
            return [self._emit_literal(expression)]

        if isinstance(expression, NameUse):
            return self._emit_name_use(expression, context)

        if isinstance(expression, FunctionCall):
            return self._emit_function_call(expression, context)

        if isinstance(expression, UnaryOp):
            return self._emit_unary_op(expression, context)

        if isinstance(expression, BinaryOp):
            return self._emit_binary_op(expression, context)

        raise CodeGenerationError(f"Expressão sem geração de código: {expression!r}.")


    def _emit_expression_with_conversion(
        self, expression: object, context: UnitContext, *, expected_type: str
    ) -> list[str]:
        instructions = self._emit_expression(expression, context)
        actual_type = self._infer_expression_type(expression, context)
        if expected_type == REAL and actual_type == INTEGER:
            instructions.append("itof")
        return instructions

    def _emit_literal(self, literal: Literal) -> str:
        if literal.type_name == INTEGER:
            return f"pushi {literal.value}"
        if literal.type_name == REAL:
            return f"pushf {literal.value}"
        if literal.type_name == LOGICAL:
            return "pushi 1" if literal.value else "pushi 0"
        if literal.type_name == STRING:
            escaped = str(literal.value).replace('"', r'\"')
            return f'pushs "{escaped}"'
        raise CodeGenerationError(f"Literal de tipo desconhecido: {literal.type_name}.")

    def _emit_name_use(self, expression: NameUse, context: UnitContext) -> list[str]:
        name = expression.name.upper()
        if expression.arguments and name in {signature.name for signature in self.semantic_report.function_signatures}:
            raise CodeGenerationError(
                f"Chamada à função {name!r} ainda não é suportada na geração EWVM da Fase 4."
            )

        symbol = context.symbol(name)
        if expression.arguments:
            return self._emit_array_address(expression, context) + ["loadn"]
        return [f"pushg {symbol.position}"]

    def _emit_array_address(self, target: NameUse, context: UnitContext) -> list[str]:
        symbol = context.symbol(target.name)
        if not symbol.dimensions:
            raise CodeGenerationError(f"Símbolo {target.name!r} não é array.")
        if len(symbol.dimensions) != 1:
            raise CodeGenerationError(
                f"Array {target.name!r} tem {len(symbol.dimensions)} dimensões; "
                "a Fase 4 suporta geração para arrays unidimensionais."
            )
        if len(target.arguments) != 1:
            raise CodeGenerationError(f"Array {target.name!r} deve receber exatamente um índice.")

        # Fortran indexa arrays a partir de 1 neste subconjunto. A posição EWVM
        # é base + índice - 1.
        return [
            "pushgp",
            *self._emit_expression(target.arguments[0], context),
            "pushi 1",
            "sub",
            f"pushi {symbol.position}",
            "add",
        ]

    def _emit_function_call(self, expression: FunctionCall, context: UnitContext) -> list[str]:
        name = expression.name.upper()
        if name == "MOD":
            if len(expression.arguments) != 2:
                raise CodeGenerationError("MOD exige exatamente dois argumentos na geração de código.")
            return (
                self._emit_expression(expression.arguments[0], context)
                + self._emit_expression(expression.arguments[1], context)
                + ["mod"]
            )
        raise CodeGenerationError(f"Função intrínseca {name!r} sem geração de código.")

    def _emit_unary_op(self, expression: UnaryOp, context: UnitContext) -> list[str]:
        if expression.operator == "-":
            # 0 - expr evita depender de uma instrução unária específica da VM.
            expression_type = self._infer_expression_type(expression.operand, context)
            zero = "pushf 0.0" if expression_type == REAL else "pushi 0"
            op = "fsub" if expression_type == REAL else "sub"
            return [zero] + self._emit_expression(expression.operand, context) + [op]

        if expression.operator == "NOT":
            return self._emit_expression(expression.operand, context) + ["not"]

        raise CodeGenerationError(f"Operador unário sem geração: {expression.operator!r}.")

    def _emit_binary_op(self, expression: BinaryOp, context: UnitContext) -> list[str]:
        left_type = self._infer_expression_type(expression.left, context)
        right_type = self._infer_expression_type(expression.right, context)
        result_numeric_type = REAL if REAL in {left_type, right_type} else INTEGER
        operator = expression.operator

        if operator in {"+", "-", "*", "/"}:
            instructions = self._emit_expression_with_conversion(
                expression.left, context, expected_type=result_numeric_type
            )
            instructions.extend(
                self._emit_expression_with_conversion(
                    expression.right, context, expected_type=result_numeric_type
                )
            )
            op_map = {
                INTEGER: {"+": "add", "-": "sub", "*": "mul", "/": "div"},
                REAL: {"+": "fadd", "-": "fsub", "*": "fmul", "/": "fdiv"},
            }
            instructions.append(op_map[result_numeric_type][operator])
            return instructions

        if operator in {"EQ", "NE", "LT", "LE", "GT", "GE"}:
            if result_numeric_type == INTEGER and left_type == LOGICAL and right_type == LOGICAL:
                result_numeric_type = LOGICAL
            instructions = self._emit_expression_with_conversion(
                expression.left, context, expected_type=result_numeric_type
            )
            instructions.extend(
                self._emit_expression_with_conversion(
                    expression.right, context, expected_type=result_numeric_type
                )
            )
            op_map = {
                INTEGER: {
                    "EQ": "equal",
                    "NE": "equal\nnot",
                    "LT": "inf",
                    "LE": "infeq",
                    "GT": "sup",
                    "GE": "supeq",
                },
                REAL: {
                    "EQ": "equal",
                    "NE": "equal\nnot",
                    "LT": "finf",
                    "LE": "finfeq",
                    "GT": "fsup",
                    "GE": "fsupeq",
                },
                LOGICAL: {
                    "EQ": "equal",
                    "NE": "equal\nnot",
                },
            }
            code = op_map[result_numeric_type][operator]
            instructions.extend(code.splitlines())
            return instructions

        if operator == "AND":
            instructions = self._emit_expression(expression.left, context)
            instructions.extend(self._emit_expression(expression.right, context))
            instructions.append("and")
            return instructions

        if operator == "OR":
            instructions = self._emit_expression(expression.left, context)
            instructions.extend(self._emit_expression(expression.right, context))
            instructions.append("or")
            return instructions

        raise CodeGenerationError(f"Operador binário sem geração: {operator!r}.")

    def _infer_expression_type(self, expression: object, context: UnitContext) -> str:
        if isinstance(expression, Literal):
            return expression.type_name

        if isinstance(expression, NameUse):
            name = expression.name.upper()
            if expression.arguments and name in {signature.name for signature in self.semantic_report.function_signatures}:
                for signature in self.semantic_report.function_signatures:
                    if signature.name == name:
                        return signature.return_type
            return context.symbol(name).type_name

        if isinstance(expression, FunctionCall):
            if expression.name.upper() == "MOD":
                return INTEGER
            raise CodeGenerationError(f"Função intrínseca desconhecida: {expression.name!r}.")

        if isinstance(expression, UnaryOp):
            if expression.operator == "NOT":
                return LOGICAL
            return self._infer_expression_type(expression.operand, context)

        if isinstance(expression, BinaryOp):
            if expression.operator in {"EQ", "NE", "LT", "LE", "GT", "GE", "AND", "OR"}:
                return LOGICAL
            left = self._infer_expression_type(expression.left, context)
            right = self._infer_expression_type(expression.right, context)
            return REAL if REAL in {left, right} else INTEGER

        raise CodeGenerationError(f"Não foi possível inferir o tipo de {expression!r}.")

    def _find_matching_continue(self, statements: list[object], start_index: int, label: int) -> int:
        for index in range(start_index + 1, len(statements)):
            statement = statements[index]
            if isinstance(statement, LabelledStatement) and statement.label == label:
                if isinstance(statement.statement, Continue):
                    return index
        raise CodeGenerationError(
            f"Não foi encontrado CONTINUE com label {label} para o DO iniciado na posição {start_index}."
        )

    def _unwrap(self, statement: object) -> object:
        return statement.statement if isinstance(statement, LabelledStatement) else statement

    def _source_label_name(self, label: int) -> str:
        return f"L{label}"

    def _source_label(self, label: int) -> str:
        return f"{self._source_label_name(label)}:"

    def _format(self, instructions: Iterable[str]) -> str:
        lines: list[str] = []
        for instruction in instructions:
            for line in instruction.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
        return "\n".join(lines) + "\n"


def generate(program: ProgramFile, semantic_report: SemanticReport) -> str:
    """Gera código EWVM a partir da AST validada e do relatório semântico."""

    return CodeGenerator(program, semantic_report).generate()
