"""Análise semântica do subconjunto de Fortran 77.

A análise semântica recebe a AST construída pelo parser e valida regras que a
sintaxe, por si só, não consegue garantir: declaração de nomes, compatibilidade
de tipos, uso correto de arrays, chamadas de funções e coerência dos labels
usados em ``DO`` e ``GOTO``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from functools import reduce
from operator import mul
from typing import Any
import json

from .ast_nodes import (
    Assignment,
    BinaryOp,
    Continue,
    Declaration,
    Do,
    Function,
    FunctionCall,
    Goto,
    If,
    LabelledStatement,
    Literal,
    NameUse,
    Print,
    Program,
    ProgramFile,
    Read,
    Return,
    UnaryOp,
    VariableDeclaration,
)
from .errors import SemanticError


INTEGER = "INTEGER"
REAL = "REAL"
LOGICAL = "LOGICAL"
STRING = "STRING"
UNKNOWN = "UNKNOWN"

NUMERIC_TYPES = {INTEGER, REAL}
ARITHMETIC_OPERATORS = {"+", "-", "*", "/"}
RELATIONAL_OPERATORS = {"EQ", "NE", "LT", "LE", "GT", "GE"}
LOGICAL_OPERATORS = {"AND", "OR"}


@dataclass
class Symbol:
    """Entrada da tabela de símbolos de uma unidade Fortran."""

    name: str
    type_name: str
    position: int
    size: int = 1
    dimensions: list[int] = field(default_factory=list)
    kind: str = "variable"

    @property
    def is_array(self) -> bool:
        return bool(self.dimensions)


@dataclass
class FunctionSignature:
    """Assinatura de uma função reconhecida no ficheiro."""

    name: str
    return_type: str
    parameters: list[str]
    parameter_types: list[str] = field(default_factory=list)


@dataclass
class UnitReport:
    """Resultado semântico de uma unidade de compilação."""

    name: str
    kind: str
    symbols: list[Symbol]
    labels: list[int]


@dataclass
class SemanticReport:
    """Resultado global da análise semântica."""

    program_name: str
    main: UnitReport
    functions: list[UnitReport]
    function_signatures: list[FunctionSignature]


class SymbolTable:
    """Tabela de símbolos local a um programa ou função."""

    def __init__(self, scope_name: str):
        self.scope_name = scope_name
        self._symbols: dict[str, Symbol] = {}
        self._next_position = 0

    def add(
        self,
        name: str,
        type_name: str,
        *,
        size: int = 1,
        dimensions: list[int] | None = None,
        kind: str = "variable",
    ) -> Symbol:
        normalised_name = name.upper()
        if normalised_name in self._symbols:
            raise SemanticError(
                f"Símbolo {normalised_name!r} já declarado no âmbito {self.scope_name!r}."
            )

        symbol = Symbol(
            name=normalised_name,
            type_name=type_name,
            position=self._next_position,
            size=size,
            dimensions=dimensions or [],
            kind=kind,
        )
        self._symbols[normalised_name] = symbol
        self._next_position += size
        return symbol

    def contains(self, name: str) -> bool:
        return name.upper() in self._symbols

    def get(self, name: str) -> Symbol:
        normalised_name = name.upper()
        if normalised_name not in self._symbols:
            raise SemanticError(
                f"Símbolo {normalised_name!r} não declarado no âmbito {self.scope_name!r}."
            )
        return self._symbols[normalised_name]

    def values(self) -> list[Symbol]:
        return list(self._symbols.values())


@dataclass
class LabelInfo:
    label: int
    statement: object
    position: int


class SemanticAnalyser:
    """Validador semântico baseado em visita à AST."""

    def __init__(self, ast: ProgramFile):
        self.ast = ast
        self.errors: list[str] = []
        self.functions: dict[str, FunctionSignature] = {}

    def analyse(self) -> SemanticReport:
        self._collect_function_signatures()

        # As funções são analisadas antes do programa principal para que as
        # chamadas feitas no programa já conheçam os tipos dos parâmetros.
        function_reports = [self._analyse_function(function) for function in self.ast.subprograms]
        main_report = self._analyse_program(self.ast.program)

        if self.errors:
            message = "Análise semântica falhou:\n- " + "\n- ".join(self.errors)
            raise SemanticError(message)

        return SemanticReport(
            program_name=self.ast.program.name,
            main=main_report,
            functions=function_reports,
            function_signatures=list(self.functions.values()),
        )

    def _collect_function_signatures(self) -> None:
        for function in self.ast.subprograms:
            name = function.name.upper()
            if name in self.functions:
                self._error(f"Função {name!r} definida mais do que uma vez.")
                continue
            self.functions[name] = FunctionSignature(
                name=name,
                return_type=function.return_type,
                parameters=[parameter.upper() for parameter in function.parameters],
            )

    def _analyse_program(self, program: Program) -> UnitReport:
        table = SymbolTable(scope_name=program.name)
        self._add_declarations(table, program.declarations, unit_name=program.name)
        labels = self._collect_labels(program.statements, unit_name=program.name)
        self._analyse_statements(
            program.statements,
            table=table,
            labels=labels,
            unit_name=program.name,
            in_function=False,
        )
        return UnitReport(
            name=program.name,
            kind="program",
            symbols=table.values(),
            labels=sorted(labels),
        )

    def _analyse_function(self, function: Function) -> UnitReport:
        table = SymbolTable(scope_name=function.name)

        try:
            table.add(function.name, function.return_type, kind="return")
        except SemanticError as error:
            self._error(str(error))

        self._add_declarations(table, function.declarations, unit_name=function.name)
        self._validate_function_parameters(function, table)

        labels = self._collect_labels(function.statements, unit_name=function.name)
        self._analyse_statements(
            function.statements,
            table=table,
            labels=labels,
            unit_name=function.name,
            in_function=True,
            function_name=function.name,
        )
        self._validate_function_return(function)

        return UnitReport(
            name=function.name,
            kind="function",
            symbols=table.values(),
            labels=sorted(labels),
        )

    def _add_declarations(
        self,
        table: SymbolTable,
        declarations: list[Declaration],
        *,
        unit_name: str,
    ) -> None:
        for declaration in declarations:
            for variable in declaration.variables:
                dimensions = self._evaluate_dimensions(variable, table, unit_name=unit_name)
                size = reduce(mul, dimensions, 1) if dimensions else 1
                kind = "function" if variable.name.upper() in self.functions else "variable"
                try:
                    table.add(
                        variable.name,
                        declaration.type_name,
                        size=size,
                        dimensions=dimensions,
                        kind=kind,
                    )
                except SemanticError as error:
                    self._error(str(error))

    def _evaluate_dimensions(
        self,
        variable: VariableDeclaration,
        table: SymbolTable,
        *,
        unit_name: str,
    ) -> list[int]:
        dimensions: list[int] = []
        for expression in variable.dimensions:
            if not isinstance(expression, Literal) or expression.type_name != INTEGER:
                self._error(
                    f"Dimensão do array {variable.name!r} em {unit_name!r} "
                    "deve ser um literal inteiro."
                )
                dimensions.append(1)
                continue
            if expression.value <= 0:
                self._error(
                    f"Dimensão do array {variable.name!r} em {unit_name!r} "
                    "deve ser positiva."
                )
                dimensions.append(1)
                continue
            dimensions.append(expression.value)
        return dimensions

    def _validate_function_parameters(self, function: Function, table: SymbolTable) -> None:
        signature = self.functions.get(function.name.upper())
        if signature is None:
            return

        parameter_types: list[str] = []
        seen: set[str] = set()
        for parameter in signature.parameters:
            if parameter in seen:
                self._error(f"Parâmetro {parameter!r} repetido na função {function.name!r}.")
            seen.add(parameter)

            if not table.contains(parameter):
                self._error(
                    f"Parâmetro {parameter!r} da função {function.name!r} não foi declarado."
                )
                parameter_types.append(UNKNOWN)
                continue

            symbol = table.get(parameter)
            if symbol.is_array:
                self._error(
                    f"Parâmetro {parameter!r} da função {function.name!r} "
                    "não pode ser declarado como array neste subconjunto."
                )
            parameter_types.append(symbol.type_name)

        signature.parameter_types = parameter_types

    def _validate_function_return(self, function: Function) -> None:
        if not self._has_assignment_to(function.statements, function.name):
            self._error(
                f"Função {function.name!r} não atribui valor ao nome da função antes do RETURN/END."
            )

    def _collect_labels(self, statements: list[object], *, unit_name: str) -> dict[int, LabelInfo]:
        labels: dict[int, LabelInfo] = {}
        counter = 0

        def visit(statement_list: list[object]) -> None:
            nonlocal counter
            for statement in statement_list:
                counter += 1
                current_position = counter
                real_statement = statement

                if isinstance(statement, LabelledStatement):
                    if statement.label in labels:
                        self._error(
                            f"Label {statement.label} repetido na unidade {unit_name!r}."
                        )
                    else:
                        labels[statement.label] = LabelInfo(
                            label=statement.label,
                            statement=statement.statement,
                            position=current_position,
                        )
                    real_statement = statement.statement

                if isinstance(real_statement, If):
                    visit(real_statement.then_statements)
                    visit(real_statement.else_statements)

        visit(statements)
        return labels

    def _analyse_statements(
        self,
        statements: list[object],
        *,
        table: SymbolTable,
        labels: dict[int, LabelInfo],
        unit_name: str,
        in_function: bool,
        function_name: str | None = None,
    ) -> None:
        counter = 0

        def visit(statement_list: list[object]) -> None:
            nonlocal counter
            for statement in statement_list:
                counter += 1
                position = counter
                real_statement = statement.statement if isinstance(statement, LabelledStatement) else statement
                self._analyse_statement(
                    real_statement,
                    table=table,
                    labels=labels,
                    unit_name=unit_name,
                    position=position,
                    in_function=in_function,
                    function_name=function_name,
                )

                if isinstance(real_statement, If):
                    visit(real_statement.then_statements)
                    visit(real_statement.else_statements)

        visit(statements)

    def _analyse_statement(
        self,
        statement: object,
        *,
        table: SymbolTable,
        labels: dict[int, LabelInfo],
        unit_name: str,
        position: int,
        in_function: bool,
        function_name: str | None,
    ) -> None:
        if isinstance(statement, Assignment):
            target_type = self._analyse_target(statement.target, table, unit_name=unit_name)
            expression_type = self._analyse_expression(statement.expression, table, unit_name=unit_name)
            self._require_assignment_compatible(target_type, expression_type, statement.target.name)
            return

        if isinstance(statement, Read):
            for item in statement.items:
                self._analyse_target(item, table, unit_name=unit_name)
            return

        if isinstance(statement, Print):
            for item in statement.items:
                self._analyse_expression(item, table, unit_name=unit_name)
            return

        if isinstance(statement, If):
            condition_type = self._analyse_expression(statement.condition, table, unit_name=unit_name)
            self._require_type(condition_type, LOGICAL, "condição do IF")
            return

        if isinstance(statement, Do):
            self._analyse_do(statement, table, labels, unit_name=unit_name, position=position)
            return

        if isinstance(statement, Goto):
            if statement.label not in labels:
                self._error(f"GOTO usa label inexistente {statement.label} em {unit_name!r}.")
            return

        if isinstance(statement, Continue):
            return

        if isinstance(statement, Return):
            if not in_function:
                self._error(f"RETURN só é permitido dentro de funções; encontrado em {unit_name!r}.")
            return

        self._error(f"Instrução sem validação semântica em {unit_name!r}: {statement!r}.")

    def _analyse_do(
        self,
        statement: Do,
        table: SymbolTable,
        labels: dict[int, LabelInfo],
        *,
        unit_name: str,
        position: int,
    ) -> None:
        if not table.contains(statement.variable):
            self._error(
                f"Variável de controlo {statement.variable!r} do DO não foi declarada em {unit_name!r}."
            )
        else:
            variable = table.get(statement.variable)
            if variable.type_name != INTEGER or variable.is_array:
                self._error(
                    f"Variável de controlo {statement.variable!r} do DO deve ser escalar INTEGER."
                )

        for description, expression in [
            ("limite inicial", statement.start),
            ("limite final", statement.end),
            ("passo", statement.step),
        ]:
            if expression is None:
                continue
            expression_type = self._analyse_expression(expression, table, unit_name=unit_name)
            self._require_type(expression_type, INTEGER, f"{description} do DO")

        label_info = labels.get(statement.end_label)
        if label_info is None:
            self._error(
                f"DO referencia label inexistente {statement.end_label} em {unit_name!r}."
            )
            return

        if not isinstance(label_info.statement, Continue):
            self._error(
                f"Label {statement.end_label} usado pelo DO em {unit_name!r} "
                "deve identificar uma instrução CONTINUE."
            )
        if label_info.position <= position:
            self._error(
                f"Label {statement.end_label} usado pelo DO em {unit_name!r} "
                "deve aparecer depois da instrução DO."
            )

    def _analyse_target(self, target: NameUse, table: SymbolTable, *, unit_name: str) -> str:
        name = target.name.upper()
        if not table.contains(name):
            self._error(f"Variável {name!r} usada sem declaração em {unit_name!r}.")
            for argument in target.arguments:
                self._analyse_expression(argument, table, unit_name=unit_name)
            return UNKNOWN

        symbol = table.get(name)
        if target.arguments:
            if not symbol.is_array:
                self._error(
                    f"Nome escalar {name!r} usado com índices em {unit_name!r}."
                )
            self._validate_array_indices(name, symbol, target.arguments, table, unit_name=unit_name)
            return symbol.type_name

        if symbol.is_array:
            self._error(
                f"Array {name!r} usado sem índice em posição de escrita em {unit_name!r}."
            )
        return symbol.type_name

    def _analyse_expression(self, expression: object, table: SymbolTable, *, unit_name: str) -> str:
        if isinstance(expression, Literal):
            return expression.type_name

        if isinstance(expression, NameUse):
            return self._analyse_name_use(expression, table, unit_name=unit_name)

        if isinstance(expression, FunctionCall):
            return self._analyse_intrinsic_call(expression, table, unit_name=unit_name)

        if isinstance(expression, UnaryOp):
            operand_type = self._analyse_expression(expression.operand, table, unit_name=unit_name)
            if expression.operator == "-":
                self._require_numeric(operand_type, "operador unário -")
                return operand_type if operand_type != UNKNOWN else UNKNOWN
            if expression.operator == "NOT":
                self._require_type(operand_type, LOGICAL, "operador .NOT.")
                return LOGICAL
            self._error(f"Operador unário desconhecido {expression.operator!r}.")
            return UNKNOWN

        if isinstance(expression, BinaryOp):
            return self._analyse_binary_op(expression, table, unit_name=unit_name)

        self._error(f"Expressão sem validação semântica em {unit_name!r}: {expression!r}.")
        return UNKNOWN

    def _analyse_name_use(self, expression: NameUse, table: SymbolTable, *, unit_name: str) -> str:
        name = expression.name.upper()

        if expression.arguments and name in self.functions:
            return self._analyse_user_function_call(expression, table, unit_name=unit_name)

        if not table.contains(name):
            self._error(f"Nome {name!r} usado sem declaração em {unit_name!r}.")
            for argument in expression.arguments:
                self._analyse_expression(argument, table, unit_name=unit_name)
            return UNKNOWN

        symbol = table.get(name)
        if expression.arguments:
            if not symbol.is_array:
                self._error(
                    f"Nome escalar {name!r} usado com argumentos/índices em {unit_name!r}."
                )
            self._validate_array_indices(name, symbol, expression.arguments, table, unit_name=unit_name)
            return symbol.type_name

        if symbol.is_array:
            self._error(
                f"Array {name!r} usado sem índice em expressão em {unit_name!r}."
            )
        return symbol.type_name

    def _analyse_user_function_call(
        self,
        expression: NameUse,
        table: SymbolTable,
        *,
        unit_name: str,
    ) -> str:
        name = expression.name.upper()
        signature = self.functions[name]

        if len(expression.arguments) != len(signature.parameters):
            self._error(
                f"Chamada à função {name!r} em {unit_name!r} recebeu "
                f"{len(expression.arguments)} argumento(s), mas esperava {len(signature.parameters)}."
            )

        for index, argument in enumerate(expression.arguments):
            argument_type = self._analyse_expression(argument, table, unit_name=unit_name)
            if index < len(signature.parameter_types):
                expected = signature.parameter_types[index]
                self._require_assignment_compatible(expected, argument_type, f"argumento {index + 1} de {name}")

        return signature.return_type

    def _analyse_intrinsic_call(
        self,
        expression: FunctionCall,
        table: SymbolTable,
        *,
        unit_name: str,
    ) -> str:
        name = expression.name.upper()
        if name != "MOD":
            self._error(f"Função intrínseca {name!r} não suportada.")
            return UNKNOWN

        if len(expression.arguments) != 2:
            self._error("MOD espera exatamente 2 argumentos.")
        for argument in expression.arguments:
            argument_type = self._analyse_expression(argument, table, unit_name=unit_name)
            self._require_type(argument_type, INTEGER, "argumento de MOD")
        return INTEGER

    def _analyse_binary_op(self, expression: BinaryOp, table: SymbolTable, *, unit_name: str) -> str:
        left_type = self._analyse_expression(expression.left, table, unit_name=unit_name)
        right_type = self._analyse_expression(expression.right, table, unit_name=unit_name)
        operator = expression.operator

        if operator in ARITHMETIC_OPERATORS:
            self._require_numeric(left_type, f"operando esquerdo de {operator}")
            self._require_numeric(right_type, f"operando direito de {operator}")
            return REAL if REAL in {left_type, right_type} else INTEGER

        if operator in RELATIONAL_OPERATORS:
            if operator in {"LT", "LE", "GT", "GE"}:
                self._require_numeric(left_type, f"operando esquerdo de .{operator}.")
                self._require_numeric(right_type, f"operando direito de .{operator}.")
            elif left_type != UNKNOWN and right_type != UNKNOWN:
                if left_type != right_type and not ({left_type, right_type} <= NUMERIC_TYPES):
                    self._error(
                        f"Operador .{operator}. recebeu tipos incompatíveis: "
                        f"{left_type} e {right_type}."
                    )
            return LOGICAL

        if operator in LOGICAL_OPERATORS:
            self._require_type(left_type, LOGICAL, f"operando esquerdo de .{operator}.")
            self._require_type(right_type, LOGICAL, f"operando direito de .{operator}.")
            return LOGICAL

        self._error(f"Operador binário desconhecido {operator!r}.")
        return UNKNOWN

    def _validate_array_indices(
        self,
        name: str,
        symbol: Symbol,
        arguments: list[object],
        table: SymbolTable,
        *,
        unit_name: str,
    ) -> None:
        if len(arguments) != len(symbol.dimensions):
            self._error(
                f"Array {name!r} em {unit_name!r} recebeu {len(arguments)} índice(s), "
                f"mas foi declarado com {len(symbol.dimensions)} dimensão(ões)."
            )
        for argument in arguments:
            argument_type = self._analyse_expression(argument, table, unit_name=unit_name)
            self._require_type(argument_type, INTEGER, f"índice do array {name}")

    def _require_assignment_compatible(self, target_type: str, expression_type: str, target_name: str) -> None:
        if UNKNOWN in {target_type, expression_type}:
            return
        if target_type == expression_type:
            return
        if target_type == REAL and expression_type == INTEGER:
            return
        self._error(
            f"Atribuição incompatível em {target_name!r}: "
            f"não é possível guardar {expression_type} em {target_type}."
        )

    def _require_type(self, actual: str, expected: str, context: str) -> None:
        if actual == UNKNOWN:
            return
        if actual != expected:
            self._error(f"{context} deve ter tipo {expected}, mas recebeu {actual}.")

    def _require_numeric(self, actual: str, context: str) -> None:
        if actual == UNKNOWN:
            return
        if actual not in NUMERIC_TYPES:
            self._error(f"{context} deve ser numérico, mas recebeu {actual}.")

    def _has_assignment_to(self, statements: list[object], name: str) -> bool:
        target_name = name.upper()
        for statement in statements:
            real_statement = statement.statement if isinstance(statement, LabelledStatement) else statement
            if isinstance(real_statement, Assignment) and real_statement.target.name.upper() == target_name:
                return True
            if isinstance(real_statement, If):
                if self._has_assignment_to(real_statement.then_statements, target_name):
                    return True
                if self._has_assignment_to(real_statement.else_statements, target_name):
                    return True
        return False

    def _error(self, message: str) -> None:
        self.errors.append(message)


def analyse(program_file: ProgramFile) -> SemanticReport:
    """Valida semanticamente a AST e devolve um relatório estruturado."""

    return SemanticAnalyser(program_file).analyse()


def _dataclass_to_dict(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _dataclass_to_dict(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, list):
        return [_dataclass_to_dict(item) for item in value]
    return value


def format_semantic_report(report: SemanticReport) -> str:
    """Formata o resultado semântico em JSON legível."""

    return json.dumps(_dataclass_to_dict(report), indent=2, ensure_ascii=False) + "\n"
