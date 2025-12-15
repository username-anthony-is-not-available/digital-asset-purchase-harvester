.PHONY: help install install-dev test test-cov test-integration test-performance lint format type-check clean pre-commit-install pre-commit-run

help:
	@echo "Available commands:"
	@echo "  make install          - Install package and dependencies"
	@echo "  make install-dev      - Install package with development dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-performance - Run performance benchmarks"
	@echo "  make lint             - Run all linters (flake8, pylint)"
	@echo "  make format           - Auto-format code with black and isort"
	@echo "  make type-check       - Run mypy type checking"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run   - Run pre-commit on all files"
	@echo "  make clean            - Remove build artifacts and cache files"

install:
	pip install -e .

install-dev:
	pip install -e .[dev]
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=digital_asset_harvester --cov-report=html --cov-report=term-missing

test-integration:
	pytest tests/integration/ -v --timeout=300

test-performance:
	pytest tests/performance/ --benchmark-only --benchmark-autosave

lint:
	flake8 digital_asset_harvester/ tests/
	pylint digital_asset_harvester/

format:
	black digital_asset_harvester/ tests/
	isort digital_asset_harvester/ tests/

type-check:
	mypy digital_asset_harvester/

pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist htmlcov .coverage .pytest_cache .mypy_cache .benchmarks
