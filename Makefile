PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: setup test smoke fresh-clone-test lint-results

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -U pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install -e .

test:
	$(BIN)/pytest -q

smoke:
	$(BIN)/python experiments/exp00_smoke/run.py

fresh-clone-test:
	bash scripts/fresh_clone_test.sh

lint-results:
	$(BIN)/python scripts/assert_results_are_code_generated.py
