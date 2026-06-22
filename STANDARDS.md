# Project Standards

This project follows the centralized standards managed by the [Intelligent Project Manager](https://github.com/username-anthony-is-not-available/intelligent-project-manager).

## Quick Reference

| Category          | Requirement                                                    |
| ----------------- | -------------------------------------------------------------- |
| **Test Coverage** | ≥80% for new code                                              |
| **Linting**       | Must pass before merge (flake8, black, isort)                  |
| **Type Safety**   | Python type hints required for all new functions               |
| **Commits**       | [Conventional Commits](https://conventionalcommits.org) format |
| **PRs**           | Require approval + passing CI                                  |
| **Secrets**       | Never committed; use env vars or vault                         |

## Full Standards

### Testing
- **Coverage**: Maintain at least 80% test coverage for all new features and bug fixes.
- **Levels**:
  - Unit tests for individual components and logic.
  - Integration tests for interactions between modules (e.g., LLM clients, exporters).
  - E2E tests for full workflows using Playwright.
- **Verification**: All existing tests must pass before any change is submitted.

### Documentation
- **Inline Comments**: Add clear comments for any complex or non-obvious logic.
- **README**: Update the main `README.md` if changes affect installation, configuration, or usage.
- **API**: Update docstrings and any external API documentation when interfaces change.
- **Changelog**: Record all notable changes in `CHANGELOG.md` following the "Keep a Changelog" format.

### Code Quality
- **Style**: Follow PEP 8 guidelines. Use `black` for formatting and `isort` for imports.
- **Linting**: Ensure `flake8` passes with no errors.
- **Cleanliness**: Remove all debug print statements, `console.log` (in JS), and commented-out code before submission.
- **Error Handling**: Implement robust error handling with appropriate logging and user feedback.

### Review and Deployment
- **Self-Review**: Perform a thorough self-review of all changes before requesting feedback.
- **PR Descriptions**: Provide detailed descriptions of what was changed and why.
- **Verification**: Verify changes in a local or dev environment that mirrors production as closely as possible.
- **Breaking Changes**: Avoid breaking changes when possible; if unavoidable, they must be clearly documented.
- **Feature Flags**: Use feature flags for new, experimental, or potentially disruptive features.

## Local Overrides

### Private Key Lifecycle & Vault Security
- **Never Log Secrets**: Private keys, mnemonics, and passphrases must never be logged to stdout, files, or any telemetry system.
- **In-Memory Only**: Decrypted private keys should only exist in-memory for the duration of the required operation.
- **Encryption at Rest**: All sensitive on-chain credentials must be stored in an encrypted vault (AES-256-GCM or equivalent) using a strong key derivation function (PBKDF2HMAC with ≥100,000 iterations).
- **Integrity Lock**: The application must fail-fast and alert the user if a vault file appears corrupted or tampered with.
- **Template Safety**: Example credential files must be suffixed with `.example` and the actual secret-containing files must be included in `.gitignore`.
