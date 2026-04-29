.PHONY: setup smoke clean

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

smoke:
	python -m src.compiler tests/fortran/exemplo_01_hello.f77 -o build/exemplo_01_hello.vm

clean:
	rm -rf build/*.vm __pycache__ src/__pycache__ .pytest_cache parser.out parsetab.py
