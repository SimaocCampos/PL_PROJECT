"""Analisador sintático para o subconjunto de Fortran 77.

O parser usa ``ply.yacc`` e constrói uma AST explícita. Nesta fase o objetivo
é reconhecer a estrutura dos programas; validações como tipos, variáveis
não declaradas e labels de ``DO`` ficam para a análise semântica.
"""

from __future__ import annotations

import ply.yacc as yacc

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
from .errors import SyntaxErrorPL
from .lexer import build_lexer, normalise_source, tokens


precedence = (
    ("left", "LOGICAL_OP"),
    ("right", "NOT_OP"),
    ("nonassoc", "REL_OP"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE"),
    ("right", "UMINUS"),
)


def _column(text: str, position: int) -> int:
    previous_newline = text.rfind("\n", 0, position)
    return position - previous_newline


def p_source(p):
    """source : optional_newlines program_unit optional_line_end subprogram_units optional_newlines"""

    p[0] = ProgramFile(program=p[2], subprograms=p[4])


def p_subprogram_units_empty(p):
    """subprogram_units : empty"""

    p[0] = []


def p_subprogram_units_many(p):
    """subprogram_units : subprogram_units function_unit optional_line_end"""

    p[0] = p[1] + [p[2]]


def p_program_unit(p):
    """program_unit : PROGRAM ID line_end declarations statements END"""

    p[0] = Program(name=p[2], declarations=p[4], statements=p[5])


def p_function_unit(p):
    """function_unit : type FUNCTION ID LPAREN parameter_list_opt RPAREN line_end declarations statements END"""

    p[0] = Function(
        return_type=p[1],
        name=p[3],
        parameters=p[5],
        declarations=p[8],
        statements=p[9],
    )


def p_type(p):
    """type : INTEGER
            | REAL
            | LOGICAL"""

    p[0] = p[1]


def p_parameter_list_opt_empty(p):
    """parameter_list_opt : empty"""

    p[0] = []


def p_parameter_list_opt_some(p):
    """parameter_list_opt : parameter_list"""

    p[0] = p[1]


def p_parameter_list_single(p):
    """parameter_list : ID"""

    p[0] = [p[1]]


def p_parameter_list_many(p):
    """parameter_list : parameter_list COMMA ID"""

    p[0] = p[1] + [p[3]]


def p_declarations_empty(p):
    """declarations : empty"""

    p[0] = []


def p_declarations_many(p):
    """declarations : declarations declaration_line"""

    p[0] = p[1] + [p[2]]


def p_declaration_line(p):
    """declaration_line : type declarator_list line_end"""

    p[0] = Declaration(type_name=p[1], variables=p[2])


def p_declarator_list_single(p):
    """declarator_list : declarator"""

    p[0] = [p[1]]


def p_declarator_list_many(p):
    """declarator_list : declarator_list COMMA declarator"""

    p[0] = p[1] + [p[3]]


def p_declarator_scalar(p):
    """declarator : ID"""

    p[0] = VariableDeclaration(name=p[1], dimensions=[])


def p_declarator_array(p):
    """declarator : ID LPAREN argument_list RPAREN"""

    p[0] = VariableDeclaration(name=p[1], dimensions=p[3])


def p_statements_empty(p):
    """statements : empty"""

    p[0] = []


def p_statements_many(p):
    """statements : statements statement_line"""

    p[0] = p[1] + [p[2]]


def p_statement_line_plain(p):
    """statement_line : statement line_end"""

    p[0] = p[1]


def p_statement_line_labelled(p):
    """statement_line : LABEL statement line_end"""

    p[0] = LabelledStatement(label=p[1], statement=p[2])


def p_statement(p):
    """statement : assignment_statement
                 | read_statement
                 | print_statement
                 | if_statement
                 | do_statement
                 | goto_statement
                 | continue_statement
                 | return_statement"""

    p[0] = p[1]


def p_assignment_statement(p):
    """assignment_statement : target ASSIGN expression"""

    p[0] = Assignment(target=p[1], expression=p[3])


def p_target_scalar(p):
    """target : ID"""

    p[0] = NameUse(name=p[1], arguments=[])


def p_target_indexed(p):
    """target : ID LPAREN argument_list RPAREN"""

    p[0] = NameUse(name=p[1], arguments=p[3])


def p_read_statement(p):
    """read_statement : READ TIMES COMMA read_item_list"""

    p[0] = Read(items=p[4])


def p_read_item_list_single(p):
    """read_item_list : target"""

    p[0] = [p[1]]


def p_read_item_list_many(p):
    """read_item_list : read_item_list COMMA target"""

    p[0] = p[1] + [p[3]]


def p_print_statement_empty(p):
    """print_statement : PRINT TIMES"""

    p[0] = Print(items=[])


def p_print_statement_items(p):
    """print_statement : PRINT TIMES COMMA print_item_list"""

    p[0] = Print(items=p[4])


def p_print_item_list_single(p):
    """print_item_list : expression"""

    p[0] = [p[1]]


def p_print_item_list_many(p):
    """print_item_list : print_item_list COMMA expression"""

    p[0] = p[1] + [p[3]]


def p_if_statement_without_else(p):
    """if_statement : IF LPAREN expression RPAREN THEN line_end statements ENDIF"""

    p[0] = If(condition=p[3], then_statements=p[7], else_statements=[])


def p_if_statement_with_else(p):
    """if_statement : IF LPAREN expression RPAREN THEN line_end statements ELSE line_end statements ENDIF"""

    p[0] = If(condition=p[3], then_statements=p[7], else_statements=p[10])


def p_do_statement_without_step(p):
    """do_statement : DO INTEGER_LITERAL ID ASSIGN expression COMMA expression"""

    p[0] = Do(end_label=p[2], variable=p[3], start=p[5], end=p[7], step=None)


def p_do_statement_with_step(p):
    """do_statement : DO INTEGER_LITERAL ID ASSIGN expression COMMA expression COMMA expression"""

    p[0] = Do(end_label=p[2], variable=p[3], start=p[5], end=p[7], step=p[9])


def p_goto_statement(p):
    """goto_statement : GOTO INTEGER_LITERAL"""

    p[0] = Goto(label=p[2])


def p_continue_statement(p):
    """continue_statement : CONTINUE"""

    p[0] = Continue()


def p_return_statement(p):
    """return_statement : RETURN"""

    p[0] = Return()


def p_expression_binary_arithmetic(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression"""

    p[0] = BinaryOp(operator=p[2], left=p[1], right=p[3])


def p_expression_binary_relation(p):
    """expression : expression REL_OP expression"""

    p[0] = BinaryOp(operator=p[2], left=p[1], right=p[3])


def p_expression_binary_logical(p):
    """expression : expression LOGICAL_OP expression"""

    p[0] = BinaryOp(operator=p[2], left=p[1], right=p[3])


def p_expression_unary_minus(p):
    """expression : MINUS expression %prec UMINUS"""

    p[0] = UnaryOp(operator="-", operand=p[2])


def p_expression_unary_not(p):
    """expression : NOT_OP expression"""

    p[0] = UnaryOp(operator="NOT", operand=p[2])


def p_expression_group(p):
    """expression : LPAREN expression RPAREN"""

    p[0] = p[2]


def p_expression_integer(p):
    """expression : INTEGER_LITERAL"""

    p[0] = Literal(value=p[1], type_name="INTEGER")


def p_expression_real(p):
    """expression : REAL_LITERAL"""

    p[0] = Literal(value=p[1], type_name="REAL")


def p_expression_string(p):
    """expression : STRING_LITERAL"""

    p[0] = Literal(value=p[1], type_name="STRING")


def p_expression_bool(p):
    """expression : BOOL_LITERAL"""

    p[0] = Literal(value=p[1], type_name="LOGICAL")


def p_expression_name(p):
    """expression : ID"""

    p[0] = NameUse(name=p[1], arguments=[])


def p_expression_name_with_arguments(p):
    """expression : ID LPAREN argument_list RPAREN"""

    p[0] = NameUse(name=p[1], arguments=p[3])


def p_expression_mod_call(p):
    """expression : MOD LPAREN argument_list RPAREN"""

    p[0] = FunctionCall(name="MOD", arguments=p[3])


def p_argument_list_single(p):
    """argument_list : expression"""

    p[0] = [p[1]]


def p_argument_list_many(p):
    """argument_list : argument_list COMMA expression"""

    p[0] = p[1] + [p[3]]


def p_optional_line_end_empty(p):
    """optional_line_end : empty"""

    p[0] = None


def p_optional_line_end_some(p):
    """optional_line_end : line_end"""

    p[0] = None


def p_optional_newlines_empty(p):
    """optional_newlines : empty"""

    p[0] = None


def p_optional_newlines_some(p):
    """optional_newlines : newlines"""

    p[0] = None


def p_line_end(p):
    """line_end : NEWLINE optional_newlines"""

    p[0] = None


def p_newlines_single(p):
    """newlines : NEWLINE"""

    p[0] = None


def p_newlines_many(p):
    """newlines : newlines NEWLINE"""

    p[0] = None


def p_empty(p):
    """empty :"""

    p[0] = None


def p_error(token):
    if token is None:
        raise SyntaxErrorPL("Fim inesperado do ficheiro durante a análise sintática.")

    source = getattr(token.lexer, "lexdata", "")
    column = _column(source, token.lexpos)
    raise SyntaxErrorPL(
        f"Erro sintático perto de {token.value!r} "
        f"(token {token.type}) na linha {token.lineno}, coluna {column}."
    )


def build_parser(**kwargs):
    """Constrói e devolve um parser PLY."""

    return yacc.yacc(start="source", **kwargs)


def parse(source: str):
    """Transforma código fonte Fortran numa AST."""

    prepared_source = normalise_source(source)
    lexer = build_lexer()
    parser = build_parser()
    return parser.parse(prepared_source, lexer=lexer)
