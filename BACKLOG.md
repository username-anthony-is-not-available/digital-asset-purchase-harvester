# Project Backlog

This backlog tracks the project milestones and upcoming tasks for the Digital Asset Purchase Harvester, aligned with the strategic priorities for 2025.

## 🎯 High Priority (2025 Strategic Priorities)

- [ ] **Improve Extraction Accuracy**: Reach 95%+ accuracy for major exchanges (Coinbase, Binance, Kraken).
- [ ] **Manual Review Workflow**: Implement a dedicated UI/workflow in the Web API for users to manually review and correct low-confidence extractions.
- [ ] **False Positive Reduction**: Implement advanced filtering or secondary LLM verification to reduce the false positive rate to <5%.
- [ ] **Performance Optimization**: Optimize the extraction pipeline to reach a processing speed of 100+ emails/min.

## 🛠️ Feature Enhancements

- [ ] **Expanded Exchange Support**: Add specialized extractors for more regional and global exchanges (e.g., Swyftx, Coinsquare, Bitpanda).
- [ ] **Enhanced Koinly Integration**: Transition from placeholder API client to full integration if/when Koinly releases a public API.
- [ ] **Multi-Currency Support for Reports**: Improve reporting for users with multi-fiat currency portfolios.
- [ ] **Tax Tool Exports**: Add support for more tax tools (e.g., ZenLedger, TokenTax).
- [ ] **On-Chain Verification UI**: Build a dashboard to visualize discrepancies between harvested data and on-chain balances.

## 🏗️ Technical Debt & Infrastructure

- [ ] **Unified Testing Suite**: Standardize tests across all extractors to ensure consistent coverage.
- [ ] **Containerization Improvements**: Optimize Docker image size and build times.
- [ ] **Advanced PII Masking**: Improve the `PIIScrubber` to handle more edge cases and varied data formats.

## ✅ Completed (Recent Milestones)

- [x] Koinly Universal CSV Export support.
- [x] Token balance verification via `blockchain-core`.
- [x] Batch processing support for `.eml` files.
- [x] Automatic fallback to Cloud LLM from local Ollama.
- [x] Standardized date formatting and UTC normalization across all exporters.
- [x] Specialized extractors for Bitstamp and Bitfinex.
