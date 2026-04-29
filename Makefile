.PHONY: setup smoke tokens ast ast-all clean

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

clean:
	rm -rf build/*.vm build/*.tokens build/*.ast.json __pycache__ src/__pycache__ .pytest_cache parser.out parsetab.py src/parser.out src/parsetab.py
