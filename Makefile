# Makefile for Digital Asset Purchase Harvester
# ==========================================
# This Makefile provides a unified interface for setting up and managing the project.
# It is designed to work on Linux/macOS and requires Python 3.7+ and make to be installed.

# Variables
# ---------
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
.DEFAULT_GOAL := help

# Phony targets
# -------------
.PHONY: help setup clean install install-dev test test-cov test-integration test-performance lint format type-check pre-commit-install pre-commit-run

# General commands
# ----------------
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  setup                - Set up the project environment"
	@echo "  install              - Install package and dependencies"
	@echo "  install-dev          - Install package with development dependencies"
	@echo "  test                 - Run all tests (excluding integration and performance)"
	@echo "  test-cov             - Run tests with coverage report"
	@echo "  test-integration     - Run integration tests only"
	@echo "  test-performance     - Run performance benchmarks"
	@echo "  lint                 - Run all linters (flake8, pylint)"
	@echo "  format               - Auto-format code with black and isort"
	@echo "  type-check           - Run mypy type checking"
	@echo "  pre-commit-install   - Install pre-commit hooks"
	@echo "  pre-commit-run       - Run pre-commit on all files"
	@echo "  clean                - Remove build artifacts, cache files, and venv"

# Setup and installation
# ----------------------
$(VENV_DIR)/bin/activate:
	@echo "📦 Creating virtual environment..."
	@python -m venv $(VENV_DIR) || (echo "❌ Failed to create virtual environment. Please ensure Python 3.7+ is installed and available as 'python'."; exit 1)

setup: $(VENV_DIR)/bin/activate
	@echo "🚀 Setting up Digital Asset Purchase Harvester..."
	@echo "📋 Installing requirements..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	@echo "🤖 Checking for Ollama..."
	@if ! command -v ollama &> /dev/null; then \
		echo "⚠️ Ollama is not installed. Please install Ollama and pull the required model:"; \
		echo "   Visit: https://ollama.ai/download"; \
		echo "   Then run: ollama pull llama3.2:3b"; \
	else \
		echo "✅ Ollama found. Make sure you have the required model:"; \
		echo "   ollama pull llama3.2:3b"; \
	fi
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "To get started:"
	@echo "1. Activate the virtual environment: source $(VENV_DIR)/bin/activate"
	@echo "2. Run tests: make test"

install: setup
	$(PIP) install -e .

install-dev: setup
	$(PIP) install -e .[dev]

# Testing
# -------
test: install-dev
	$(PYTHON) -m pytest -m "not integration and not performance"

test-cov: install-dev
	$(PYTHON) -m pytest --cov=digital_asset_harvester --cov-report=term-missing -m "not integration and not performance"

test-integration: install-dev
	$(PYTHON) -m pytest -m integration

test-performance: install-dev
	$(PYTHON) -m pytest -m performance

# Code quality
# ------------
lint: install-dev
	$(PYTHON) -m flake8 digital_asset_harvester/ tests/
	$(PYTHON) -m pylint digital_asset_harvester/

format: install-dev
	$(PYTHON) -m black digital_asset_harvester/ tests/
	$(PYTHON) -m isort digital_asset_harvester/ tests/

type-check: install-dev
	$(PYTHON) -m mypy digital_asset_harvester/

# Pre-commit
# ----------
pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

# Cleanup
# -------
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist htmlcov .coverage .pytest_cache .mypy_cache .benchmarks $(VENV_DIR)
