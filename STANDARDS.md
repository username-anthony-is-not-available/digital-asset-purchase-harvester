# Project Standards

This project follows the centralized standards managed by the [Intelligent Project Manager](https://github.com/username-anthony-is-not-available/intelligent-project-manager).

## Quick Reference

| Category          | Requirement                                                    |
| ----------------- | -------------------------------------------------------------- |
| **Test Coverage** | ≥80% for new code                                              |
| **Linting**       | Must pass before merge                                         |
| **Type Safety**   | TypeScript strict mode / Python type hints                     |
| **Commits**       | [Conventional Commits](https://conventionalcommits.org) format |
| **PRs**           | Require approval + passing CI                                  |
| **Secrets**       | Never committed; use env vars                                  |

## Full Standards

For complete details, see:
→ [Global STANDARDS.md](https://github.com/username-anthony-is-not-available/intelligent-project-manager/blob/main/.agent/workflows/templates/STANDARDS.md)

## Local Overrides

<!--
Add project-specific standards that EXTEND (not weaken) the global standards.
Example:
- Test coverage requirement: 90% (stricter than 80% global minimum)
- Additional required reviewers for smart contract changes
-->

### Private Key Lifecycle & Vault Security
- **Never Log Secrets**: Private keys, mnemonics, and passphrases must never be logged to stdout, files, or any telemetry system.
- **In-Memory Only**: Decrypted private keys should only exist in-memory for the duration of the required operation.
- **Encryption at Rest**: All sensitive on-chain credentials must be stored in an encrypted vault (AES-256-GCM or equivalent) using a strong key derivation function (PBKDF2HMAC with ≥100,000 iterations).
- **Integrity Lock**: The application must fail-fast and alert the user if a vault file appears corrupted or tampered with.
- **Template Safety**: Example credential files must be suffixed with `.example` and the actual secret-containing files must be included in `.gitignore`.
