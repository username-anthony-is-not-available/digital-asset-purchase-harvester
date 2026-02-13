# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Parallel Processing**: Support for parallel email processing in CLI using `ThreadPoolExecutor`.
  - New `--parallel` flag to enable concurrency.
  - New `--max-workers` argument to control parallelism.
- **New Specialized Extractors**: Added regex-based extractors for Gemini, Crypto.com, and FTX.
- **Improved Binance Extraction**: More robust transaction ID and fee extraction by searching full email content.
- **Enhanced Email Filtering**: Added more non-purchase patterns (security alerts, logins, etc.) to reduce false positives.
- **Detailed Processing Metrics**: Added tracking for regex vs LLM extractions, preprocessing skips, and failures.
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
- Implemented `ThreadPoolExecutor` pattern for I/O-bound email processing tasks.
- Added type normalization for extracted numeric fields (amount, total_spent, fee_amount).
- Added `tests/__init__.py` and subdirectory init files to ensure correct test collection in CI.
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
