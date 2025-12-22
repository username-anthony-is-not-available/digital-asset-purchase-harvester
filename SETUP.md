# Setup Guide

This guide provides detailed instructions for setting up the project environment using the unified `Makefile`. This is the recommended approach for all users.

## Prerequisites

- **Python 3.7+**: Required for running the project.
- **make**: Required for using the `Makefile`.
- **Ollama**: Required for running the LLM-based email parsing.

## Quick Start

1. **Set up the project environment**:
   ```sh
   make setup
   ```
   This command will:
   - Check for Python 3 installation.
   - Create a virtual environment in the `venv` directory.
   - Upgrade pip to the latest version.
   - Install all required dependencies from `requirements.txt` and `requirements-dev.txt`.
   - Check for Ollama installation and provide instructions if it's not found.

2. **Activate the virtual environment**:
   ```sh
   source venv/bin/activate
   ```

3. **Run the tests**:
   ```sh
   make test
   ```

## Makefile Targets

The `Makefile` provides a number of targets to simplify development:

| Target                 | Description                                                 |
| ---------------------- | ----------------------------------------------------------- |
| `make help`            | Display the help message.                                   |
| `make setup`           | Set up the project environment.                             |
| `make install`         | Install the package and dependencies.                       |
| `make install-dev`     | Install the package with development dependencies.          |
| `make test`            | Run all tests (excluding integration and performance).      |
| `make test-cov`        | Run tests with a coverage report.                           |
| `make test-integration`| Run integration tests only.                                 |
| `make test-performance`| Run performance benchmarks.                                 |
| `make lint`            | Run all linters (flake8, pylint).                           |
| `make format`          | Auto-format code with black and isort.                      |
| `make type-check`      | Run mypy type checking.                                     |
| `make pre-commit-install` | Install pre-commit hooks.                                   |
| `make pre-commit-run`  | Run pre-commit on all files.                                |
| `make clean`           | Remove build artifacts, cache files, and the venv.          |
