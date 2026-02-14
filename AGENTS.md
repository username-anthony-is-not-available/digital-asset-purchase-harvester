# AGENTS.md

This document provides instructions for AI agents working on the Digital Asset Purchase Harvester codebase.

## Project Overview

The Digital Asset Purchase Harvester is a Python tool designed to extract cryptocurrency purchase information from emails. It supports parsing emails from mbox files, Gmail, and IMAP servers, using a local or cloud-based LLM to extract purchase details. The project also includes a web UI for interactive use.

## Core Technologies

- **Backend**: Python, FastAPI
- **Frontend**: Jinja2 templates, vanilla JavaScript
- **Testing**: pytest, Playwright for E2E tests
- **LLM Integration**: Ollama (local), OpenAI, Anthropic (cloud)
- **Dependency Management**: pip, venv

## Development Setup

To set up the development environment, follow these steps:

1.  **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -e .
    ```

## Codebase Structure

-   `digital_asset_harvester/`: Main application code.
    -   `cli.py`: Command-line interface logic.
    -   `config.py`: Application configuration.
    -   `exporters/`: Modules for exporting data (e.g., to Koinly CSV).
    -   `ingest/`: Modules for reading emails from different sources (mbox, Gmail, IMAP).
    -   `llm/`: LLM client implementations and factory.
    -   `processing/`: Core logic for email parsing and data extraction.
    -   `prompts/`: LLM prompt templates.
    -   `validation/`: Data validation schemas and logic.
    -   `web/`: FastAPI web application.
-   `tests/`: Tests for the application.
    -   `e2e/`: End-to-end tests using Playwright.
    -   `fixtures/`: Test data and fixtures.
    -   `integration/`: Integration tests that may require external services (e.g., a running Ollama instance).
-   `docs/`: Project documentation.

## Development Workflow

### Adding a New Feature

1.  **Create a new branch**:
    ```bash
    git checkout -b feature/your-feature-name
    ```
2.  **Write tests**: Add unit, integration, or E2E tests for the new feature.
3.  **Implement the feature**: Write the code to make the tests pass.
4.  **Update documentation**: If the feature changes the user interface, command-line options, or API, update the relevant documentation (e.g., `README.md`, `docs/`).
5.  **Run pre-commit checks**:
    ```bash
    pre-commit run --all-files
    ```
6.  **Commit your changes**:
    ```bash
    git commit -m "feat: Add your feature description"
    ```
7.  **Push your changes and create a pull request**.

### Fixing a Bug

1.  **Create a new branch**:
    ```bash
    git checkout -b fix/your-bug-fix-name
    ```
2.  **Write a failing test**: Add a test that reproduces the bug.
3.  **Fix the bug**: Modify the code to make the test pass.
4.  **Run all tests**: Make sure your fix doesn't break anything else.
    ```bash
    pytest
    ```
5.  **Run pre-commit checks**:
    ```bash
    pre-commit run --all-files
    ```
6.  **Commit your changes**:
    ```bash
    git commit -m "fix: Add your bug fix description"
    ```
7.  **Push your changes and create a pull request**.

## Important Commands

-   **Run all tests**:
    ```bash
    pytest
    ```
-   **Run tests without integration tests**:
    ```bash
    pytest -m "not integration"
    ```
-   **Run Playwright E2E tests**:
    ```bash
    playwright install
    pytest tests/e2e/
    ```
-   **Run linters and formatters**:
    ```bash
    pre-commit run --all-files
    ```
-   **Run the web UI**:
    ```bash
    python -m digital_asset_harvester.web.run
    ```
-   **Run the CLI**:
    ```bash
    digital-asset-harvester --help
    ```

## Code Style and Conventions

-   Follow the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).
-   Use type hints for all function signatures.
-   Write clear and concise commit messages.
-   Keep pull requests focused on a single issue.

## Pre-Commit Checks

This project uses `pre-commit` to enforce code style and run static analysis checks. Before submitting a change, run the following command to make sure your code passes all checks:

```bash
pre-commit run --all-files
```

This will automatically fix some issues and report others that need manual attention. Make sure all checks pass before creating a pull request.
