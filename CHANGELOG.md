# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **New Exchange Extractors**: Added specialized regex-based extractors for Bitstamp and Bitfinex to improve extraction speed and accuracy.
- **Enhanced FX Rate Service**: Improved `FXRateService` with robust date parsing via `dateutil.parser` and a reliable retry mechanism for external API calls.
- **Improved CRA PDF Export**: Enhanced the CRA report grouping logic to group summaries first by currency, then by vendor, including subtotals for clearer financial reporting.
- **Standardized Date Formatting**: Unified date formatting across all exporters (`cointracker.py`, `koinly.py`, `cryptotaxcalculator.py`) using `dateutil.parser` with UTC normalization.
- **Token Balance Verification**: Cross-reference harvested purchases with actual on-chain balances.
  - New `BlockchainVerifier` integration using `blockchain-core`.
  - Configurable wallet addresses via `DAP_BLOCKCHAIN_WALLETS`.
  - CLI support via `--verify` flag.
  - Detailed discrepancy reporting in logs.

- **EML File Support**: Batch processing of individual `.eml` files.
  - New `EmlDataExtractor` for directory-based ingestion.
  - CLI support via `--eml-dir` argument.
  - Web UI support for multiple `.eml` file uploads.

- **Ollama Auto-Fallback**: Automatic fallback to Cloud LLM if local Ollama is too slow.
  - New `FallbackLLMClient` to handle provider switching.
  - Configuration options: `enable_ollama_fallback`, `ollama_fallback_threshold_seconds`, `fallback_cloud_provider`.
  - Seamless integration with existing `get_llm_client` factory.

- **Koinly CSV Export**: Added support for exporting transactions in Koinly Universal CSV format
  - New `KoinlyReportGenerator` class for generating Koinly-compatible CSV files
  - `write_purchase_data_to_koinly_csv()` function for easy CSV export
  - Feature flag `enable_koinly_csv_export` (env: `DAP_ENABLE_KOINLY_CSV_EXPORT`)
  - CLI option `--output-format koinly` to export in Koinly format

- **Koinly API Integration (Placeholder)**: Future-ready API client for direct transaction upload
  - New `KoinlyApiClient` class in `digital_asset_harvester.integrations`
  - Feature flag `enable_koinly_api` (env: `DAP_ENABLE_KOINLY_API`)
  - Configuration options: `koinly_api_key`, `koinly_portfolio_id`, `koinly_api_base_url`
  - CLI option `--koinly-upload` for direct API uploads
  - Informative error messages explaining Koinly's current API limitations
  - Automatic fallback to CSV export when API is not available

### Technical Details
- Added new `integrations` module for external service integrations
- Comprehensive test coverage (18 new tests for Koinly functionality)
- Proper error handling and logging for Koinly operations
- Context manager support for `KoinlyApiClient`
- Timezone-aware datetime handling in CSV exports

### Documentation
- Updated README with Koinly integration instructions
- Added manual upload process documentation
- Included configuration examples for both CSV and API methods

## Notes
**Important**: Koinly does not currently provide a public API for transaction uploads. The API client is designed as a placeholder that will be ready if/when Koinly releases an API. Users should use the CSV export feature for now.
