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

pilots:
	$(BIN)/python experiments/exp01_pilot_h1/run.py
	$(BIN)/python experiments/exp02_pilot_h2/run.py
	$(BIN)/python experiments/exp03_pilot_h3/run.py

fresh-clone-test:
	bash scripts/fresh_clone_test.sh

lint-results:
	$(BIN)/python scripts/assert_results_are_code_generated.py
