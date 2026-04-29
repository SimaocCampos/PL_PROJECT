.PHONY: setup smoke tokens clean

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

smoke:
	python -m src.compiler tests/fortran/exemplo_01_hello.f77 -o build/exemplo_01_hello.vm

tokens:
	python -m src.compiler tests/fortran/exemplo_02_fatorial.f77 --tokens

clean:
	rm -rf build/*.vm build/*.tokens __pycache__ src/__pycache__ .pytest_cache parser.out parsetab.py
