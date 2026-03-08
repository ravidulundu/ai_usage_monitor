PYTHON ?= ./.venv/bin/python
BOOTSTRAP_PYTHON ?= python3

.PHONY: help setup hooks-install hooks-run check lint lint-qml format format-check test typecheck health-quick health health-ci

help:
	@echo "Available targets:"
	@echo "  make setup         # install dev deps + git hooks"
	@echo "  make format        # apply Python formatting"
	@echo "  make lint          # quick quality gates"
	@echo "  make check         # full quality gates (includes tests)"
	@echo "  make test          # run pytest"
	@echo "  make typecheck     # run mypy on Python core"
	@echo "  make hooks-install # install pre-commit hooks"
	@echo "  make hooks-run     # run pre-commit on all files"

setup:
	test -d .venv || $(BOOTSTRAP_PYTHON) -m venv .venv
	./.venv/bin/python -m pip install --upgrade pip
	./.venv/bin/python -m pip install -r requirements-dev.txt
	npm ci
	./.venv/bin/pre-commit install

health-quick:
	$(PYTHON) tools/project_health_check.py --mode quick

health:
	$(PYTHON) tools/project_health_check.py --mode full

health-ci:
	$(PYTHON) tools/project_health_check.py --mode ci --fail-on-warn

check: health

lint: health-quick

lint-qml:
	tools/run_qmllint.sh

format:
	$(PYTHON) -m ruff format core tests com.aiusagemonitor/contents/scripts gnome-extension/aiusagemonitor@aimonitor/scripts bin/ai-usage-monitor-state

format-check:
	$(PYTHON) -m ruff format --check core tests com.aiusagemonitor/contents/scripts gnome-extension/aiusagemonitor@aimonitor/scripts bin/ai-usage-monitor-state

typecheck:
	PYTHONPATH=. $(PYTHON) -m mypy --config-file mypy.ini

test:
	$(PYTHON) -m pytest -q

hooks-install:
	./.venv/bin/pre-commit install

hooks-run:
	./.venv/bin/pre-commit run --all-files
