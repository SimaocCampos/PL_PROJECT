.PHONY: setup smoke tokens ast ast-all semantic semantic-all invalid-all clean

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

smoke:
	python -m src.compiler tests/fortran/exemplo_01_hello.f77 -o build/exemplo_01_hello.vm

tokens:
	python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --tokens

ast:
	python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --ast

ast-all:
	python -m src.compiler tests/fortran/exemplo_01_hello.f77 --ast-output build/exemplo_01_hello.ast.json
	python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --ast-output build/exemplo_02_fatorial.ast.json
	python -m src.compiler tests/fortran/exemplo_03_primo.f77 --ast-output build/exemplo_03_primo.ast.json
	python -m src.compiler tests/fortran/exemplo_04_soma_array.f77 --ast-output build/exemplo_04_soma_array.ast.json
	python -m src.compiler tests/fortran/exemplo_05_conversor_function.f77 --ast-output build/exemplo_05_conversor_function.ast.json

semantic:
	python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --semantic

semantic-all:
	python -m src.compiler tests/fortran/exemplo_01_hello.f77 --semantic-output build/exemplo_01_hello.semantic.json
	python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --semantic-output build/exemplo_02_fatorial.semantic.json
	python -m src.compiler tests/fortran/exemplo_03_primo.f77 --semantic-output build/exemplo_03_primo.semantic.json
	python -m src.compiler tests/fortran/exemplo_04_soma_array.f77 --semantic-output build/exemplo_04_soma_array.semantic.json
	python -m src.compiler tests/fortran/exemplo_05_conversor_function.f77 --semantic-output build/exemplo_05_conversor_function.semantic.json

invalid-all:
	- python -m src.compiler tests/invalid/undeclared_var.f77 --semantic
	- python -m src.compiler tests/invalid/type_error.f77 --semantic
	- python -m src.compiler tests/invalid/missing_label.f77 --semantic
	- python -m src.compiler tests/invalid/duplicate_var.f77 --semantic
	- python -m src.compiler tests/invalid/array_index_type.f77 --semantic
	- python -m src.compiler tests/invalid/wrong_do_label.f77 --semantic
	- python -m src.compiler tests/invalid/return_in_program.f77 --semantic

clean:
	rm -rf build/*.vm build/*.tokens build/*.ast.json build/*.semantic.json __pycache__ src/__pycache__ .pytest_cache parser.out parsetab.py src/parser.out src/parsetab.py
