# Digital Asset Purchase Harvester

[![CI](https://github.com/username-anthony-is-not-available/digital-asset-purchase-harvester/actions/workflows/ci.yml/badge.svg)](https://github.com/username-anthony-is-not-available/digital-asset-purchase-harvester/actions/workflows/ci.yml)

A Python tool to extract cryptocurrency purchase information from email data stored in mbox files. This project aims to help crypto enthusiasts quickly parse their email history for purchase records.

## ⚠️ Important Notes

- This is a helper tool, not a production-ready solution
- Results may be incomplete or inaccurate - always verify the data
- The project is not actively maintained
- Uses local LLM (Ollama) for email parsing and analysis

## 🐳 Docker Quick Start

Get started with Docker in one command:

```bash
./setup.sh
```

This automated setup script will:
- Check and install Docker if needed
- Build the Docker image
- Set up Ollama service with the required model
- Start all services with docker-compose

**Manual Docker commands:**

```bash
# Build and start services
docker compose up -d

# Run the harvester
docker compose exec harvester digital-asset-harvester --help

# Process emails
docker compose exec harvester digital-asset-harvester \
  --mbox-file /app/your_emails.mbox \
  --output /app/output/crypto_purchases.csv

# View logs
docker compose logs -f

# Stop services
docker compose down
```

> **Note**: Place your `.mbox` files in the project directory - they will be accessible in the container at `/app/`. Output files are saved to `./output/`.

## ⚡ Quick Start

1. **Set up the project environment**:

   **Windows (PowerShell):**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -e .
   ```

   **Linux/macOS:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Test the setup**:

   ```sh
   pytest
   ```

3. **Process your emails**:

   - **From an mbox file:**
     ```sh
     digital-asset-harvester --mbox-file your_emails.mbox --output crypto_purchases.csv
     ```
   - **Directly from Gmail:**
     ```sh
     digital-asset-harvester --gmail --output crypto_purchases.csv
     ```
   - **From an IMAP server:**
      ```sh
      digital-asset-harvester --imap --imap-server imap.example.com --imap-user user@example.com --output crypto_purchases.csv
      ```
     _(or run `python -m digital_asset_harvester.cli` if you prefer module execution)_

## 🌐 Web UI

The Digital Asset Purchase Harvester now includes an interactive web interface for processing email files.

### Starting the Web Server

```sh
python -m digital_asset_harvester.web.run
```

The web interface will be available at `http://localhost:8000`

### Using the Web UI

1. **Upload**: Navigate to the home page and upload your mbox file
2. **Processing**: The file will be processed in the background, and you'll see a real-time status page
3. **Results**: Once complete, view extracted purchases in a sortable table
4. **Export**: Download results in CSV or JSON format

The web UI provides:
- 📤 File upload with background processing
- 📊 Real-time processing status updates
- 📋 Interactive table display with sortable columns
- 💾 Export options (CSV and JSON)
- 🔄 Process multiple files sequentially

## 📦 Install from source

You can install the package locally in editable mode to get the console script:

```sh
pip install -e .
```

Install development dependencies (tests, linting, docs) with:

```sh
pip install -e .[dev]
```

## 🛠️ Build a distribution

Create a wheel and source distribution using the Python build tool:

```sh
pip install build
python -m build
```

Artifacts will appear under `dist/` and can be uploaded to a package index of your choice.

## 🚀 Recent Improvements

### Enhanced Email Detection

- **Smart Preprocessing**: Filters out newsletters, marketing emails, and non-purchase content before LLM analysis
- **Comprehensive Keyword Detection**: Recognizes 30+ major cryptocurrency exchanges and 50+ crypto terms
- **Improved Classification Prompts**: Better LLM prompts with specific examples and exclusion criteria

### Better Accuracy & Performance

- **Confidence Scoring**: Each detection includes a confidence score to help identify uncertain results
- **Data Validation**: Validates extracted data for completeness and reasonableness
- **Faster Processing**: Pre-filtering reduces unnecessary LLM calls by ~70% for typical email sets
- **Enhanced Error Handling**: Robust error handling with detailed logging and retry mechanisms

### Supported Exchanges & Platforms

- **Major Exchanges**: Coinbase, Binance, Kraken, Gemini, Bitfinex, Bitstamp, and 25+ others
- **Regional Platforms**: Coinspot, BTCMarkets, Swyftx (AU), Coinsquare, Newton (CA), and more
- **Cryptocurrency Coverage**: Bitcoin, Ethereum, Litecoin, and 30+ major cryptocurrencies

## Features

- Extracts email data from mbox files with improved accuracy
- Intelligent cryptocurrency purchase email identification
- Extracts detailed purchase information: amounts, currencies, vendors, dates, and transaction IDs
- Advanced preprocessing to filter out irrelevant emails
- Confidence scoring and data validation
- Comprehensive logging and error reporting
- Outputs extracted data to CSV format
- Resilient LLM client wrapper with automatic retries and JSON parsing
- Dedicated validation module with typed purchase schemas and reusable validators
- Configurable prompt templates with reusable manager
- Structured logging and lightweight metrics summary reporting

### Cloud LLM Support (OpenAI, Anthropic)

In addition to the default local LLM (Ollama), the harvester now supports cloud-based LLM providers.

- **Enable Cloud Providers**: Set the `DAP_ENABLE_CLOUD_LLM` environment variable to `true`.
- **Select a Provider**: Use `DAP_LLM_PROVIDER` to choose between `ollama`, `openai`, or `anthropic`.
- **API Keys**: Provide the appropriate API key for your chosen cloud provider:
  - `DAP_OPENAI_API_KEY`
  - `DAP_ANTHROPIC_API_KEY`

#### Ollama Auto-Fallback

If you have a slow computer and local Ollama processing takes too long, you can enable automatic fallback to a cloud provider.

- **Enable Fallback**: Set `DAP_ENABLE_OLLAMA_FALLBACK=true`.
- **Threshold**: Set the timeout threshold in seconds using `DAP_OLLAMA_FALLBACK_THRESHOLD_SECONDS` (default: 10).
- **Cloud Provider**: Specify the fallback cloud provider with `DAP_FALLBACK_CLOUD_PROVIDER` (default: `openai`).

When enabled, if Ollama takes longer than the threshold, the harvester will automatically switch to the configured cloud provider for that email.

Example configuration:

```sh
export DAP_ENABLE_CLOUD_LLM=true
export DAP_LLM_PROVIDER=openai
export DAP_OPENAI_API_KEY="your-openai-api-key"
```

## Documentation

- **[Exchange-Specific Email Format Guides](docs/EXCHANGE_FORMATS.md)**: A reference for the email formats used by various cryptocurrency exchanges.
- **[Ollama Setup Guide for Windows](docs/OLLAMA_SETUP_WINDOWS.md)**: Detailed instructions for installing and configuring Ollama on Windows (Native or WSL2).

## Project Structure

```
digital_asset_harvester/
├── cli.py             # CLI entry point
├── config.py          # Configuration handling
├── ingest/            # Email ingestion (mbox, Gmail, IMAP)
├── llm/               # LLM clients
├── output/            # CSV output utilities
├── processing/        # Extraction logic
├── web/               # Web UI (FastAPI)
└── validation/        # Data validation
```

## Requirements

- Python 3.7+
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/digital-asset-purchase-harvester.git
   cd digital-asset-purchase-harvester
   ```

2. Create and activate a virtual environment:

   **Windows (PowerShell):**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **Windows (Command Prompt):**

   ```cmd
   python -m venv venv
   venv\Scripts\activate.bat
   ```

   **Linux/macOS:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```

   > **Note**: Always activate the virtual environment before running the script or installing packages. You should see `(venv)` in your terminal prompt when the virtual environment is active.

## Usage

> **Important**: Always activate the virtual environment before running any commands!

**Windows:**

```powershell
.\venv\Scripts\Activate.ps1  # PowerShell
# or
venv\Scripts\activate.bat    # Command Prompt
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

1. Run the script:

   - **From an mbox file:**
     ```sh
     digital-asset-harvester --mbox-file path/to/your.mbox --output path/to/output.csv
     ```
   - **Directly from Gmail:**
     ```sh
     digital-asset-harvester --gmail --output path/to/output.csv
     ```

### Koinly CSV Export

The Digital Asset Purchase Harvester can generate a CSV file compatible with Koinly's "universal" format for manual import. This allows you to easily upload your transaction data to Koinly for tax reporting.

To use the Koinly CSV export, you must enable the `enable_koinly_csv_export` feature flag in your configuration. You can do this by setting the `DAP_ENABLE_KOINLY_CSV_EXPORT` environment variable to `true`:

```sh
export DAP_ENABLE_KOINLY_CSV_EXPORT=true
```

Once the feature flag is enabled, you can generate the Koinly-compatible CSV file by specifying `koinly` as the `--output-format`:

```sh
digital-asset-harvester --mbox-file your_emails.mbox --output-format koinly --output koinly_transactions.csv
```

This will create a `koinly_transactions.csv` file in the correct format for manual upload to Koinly.

### Blockchain Balance Verification

The harvester can verify your harvested totals against actual on-chain wallet balances using the `blockchain-core` library.

To enable this feature:
1. Set the `DAP_ENABLE_BLOCKCHAIN_VERIFICATION` environment variable to `true`.
2. Provide your wallet addresses using the `DAP_BLOCKCHAIN_WALLETS` environment variable as a comma-separated list of `ASSET:ADDRESS` pairs.

Example:
```sh
export DAP_ENABLE_BLOCKCHAIN_VERIFICATION=true
export DAP_BLOCKCHAIN_WALLETS="BTC:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa,ETH:0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"
```

Then run the harvester with the `--verify` flag:
```sh
digital-asset-harvester --mbox-file your_emails.mbox --verify
```

A verification report will be displayed in the logs, showing matches and discrepancies.

### Koinly API Integration (Experimental)

**Note:** Koinly does not currently provide a public API for uploading transactions. The API integration feature is implemented as a placeholder for future compatibility.

The harvester includes a Koinly API client that is designed to support direct transaction uploads when Koinly releases an API. To enable this feature:

```sh
export DAP_ENABLE_KOINLY_API=true
export DAP_KOINLY_API_KEY=your_api_key
export DAP_KOINLY_PORTFOLIO_ID=your_portfolio_id
```

Then use the `--koinly-upload` flag:

```sh
digital-asset-harvester --mbox-file your_emails.mbox --koinly-upload
```

**Current Status:** When the API upload is attempted, the client will provide informative error messages and automatically fall back to CSV export. The CSV file can then be manually uploaded through Koinly's web interface at https://app.koinly.io.

**Manual Upload Process:**
1. Generate a Koinly CSV file as described above
2. Log in to your Koinly account
3. Navigate to: Wallets > Add Wallet > File Import
4. Upload the generated CSV file
5. Review and confirm the imported transactions

2. The script will process the mbox file and output the purchase data to the specified CSV file.

3. When finished, deactivate the virtual environment:

   ```sh
   deactivate
   ```

## Configuration

Configuration is centralized in `digital_asset_harvester/config.py`, which defines a typed `HarvesterSettings` dataclass. Use the helper functions to access or override settings:

```python
from digital_asset_harvester import get_settings, get_settings_with_overrides

settings = get_settings()
customised = get_settings_with_overrides(llm_model_name="gemma3:4b")
```

### Environment overrides

Every field can be overridden with environment variables using the `DAP_` prefix. For example:

```powershell
set DAP_LLM_MODEL_NAME=gemma3:4b
set DAP_ENABLE_PREPROCESSING=false
set DAP_MIN_CONFIDENCE_THRESHOLD=0.75
set DAP_LOG_JSON_OUTPUT=true
```

### Programmatic overrides

Call `reload_settings()` to refresh the cached settings after changing environment variables or advanced configuration:

```python
from digital_asset_harvester import reload_settings

reload_settings()
```

## Testing the Improvements

Run the test suite to validate the detection capabilities:

```sh
pytest
```

This will test various email scenarios including:

- Coinbase, Binance, and Kraken purchase confirmations
- Newsletter and price alert filtering
- Processing speed improvements

## Example Usage

```sh
# Basic usage
digital-asset-harvester --mbox-file example.mbox --output output/purchase_data.csv

# The improved system will now:
# 1. Pre-filter emails using keyword detection
# 2. Use enhanced LLM prompts for better accuracy
# 3. Validate extracted data for quality
# 4. Provide detailed processing statistics
```

### Configuration File Overrides

Advanced defaults can be configured in a TOML configuration file (default: `config/config.toml`).

```toml
[harvester]
llm_model_name = "llama3.2:3b"
min_confidence_threshold = 0.6
enable_preprocessing = true
strict_validation = true
enable_debug_output = false
```

### LLM client customization

The application now uses a factory function, `get_llm_client`, to create the appropriate LLM client based on the current settings. You can still provide a custom client to the `EmailPurchaseExtractor`:

```python
from digital_asset_harvester import EmailPurchaseExtractor, get_llm_client, get_settings_with_overrides

# Example of using the factory with custom settings
settings = get_settings_with_overrides(llm_provider="openai", enable_cloud_llm=True)
llm_client = get_llm_client(provider="openai")
extractor = EmailPurchaseExtractor(settings=settings, llm_client=llm_client)
```

### Validation utilities

All extracted purchase records flow through `PurchaseValidator`, which enforces numeric sanity checks, ISO currency formatting, and vendor/date presence. You can swap in your own validator or disable strict mode via configuration:

```python
from digital_asset_harvester import EmailPurchaseExtractor, PurchaseValidator, get_settings_with_overrides

settings = get_settings_with_overrides(strict_validation=False)
validator = PurchaseValidator(allow_unknown_crypto=False)
extractor = EmailPurchaseExtractor(settings=settings)
extractor.validator = validator
```

### Prompt customization

Prompts are stored centrally via `PromptManager`. You can supply custom templates at runtime:

```python
from digital_asset_harvester import EmailPurchaseExtractor, PromptManager, get_settings

settings = get_settings()
prompts = PromptManager()
prompts.register("classification", "Custom classification prompt for ${email_content}")
prompts.register("extraction", "Custom extraction prompt for ${email_content}")

extractor = EmailPurchaseExtractor(settings=settings, prompts=prompts)
```

### Telemetry

Enable JSON-formatted logs and capture processing metrics with the built-in telemetry helpers:

```python
from digital_asset_harvester import MetricsTracker, StructuredLoggerFactory, log_event

factory = StructuredLoggerFactory(json_output=True)
logger = factory.build("demo", default_fields={"component": "demo"})
metrics = MetricsTracker()

metrics.increment("emails_processed")
log_event(logger, "demo_event", status="ok")
```

## Virtual Environment Management

### Creating a New Environment

If you need to recreate the virtual environment:

```sh
# Remove existing environment
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# Create new environment
python -m venv venv
```

### Development Setup

For contributors, install development dependencies:

```sh
# After activating virtual environment
pip install -r requirements-dev.txt
```

### Troubleshooting

**Virtual Environment Issues:**

- **"venv not recognized"**: Make sure you're in the project directory
- **Permission errors on Windows**: Run PowerShell as Administrator or use Command Prompt
- **Python not found**: Ensure Python 3.7+ is installed and in your PATH

**Ollama Issues:**

- **Model not found**: Run `ollama pull llama3.2:3b` to download the model
- **Ollama not running**: Start Ollama service or desktop application
- **Connection errors**: Check if Ollama is running on the default port (11434)

**Import Errors:**

- Always ensure virtual environment is activated before running scripts
- Reinstall requirements: `pip install --force-reinstall -r requirements.txt`

### Environment Variables

You can set these environment variables to customize behavior:

```sh
# Windows
set OLLAMA_HOST=http://localhost:11434
set PYTHONPATH=%PYTHONPATH%;.

# Linux/macOS
export OLLAMA_HOST=http://localhost:11434
export PYTHONPATH=$PYTHONPATH:.
```

## Gmail API Setup

To use the Gmail integration, you need to enable the Gmail API and create credentials.

1. **Enable the Gmail API:**

   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - In the API Library, search for "Gmail API" and enable it.

2. **Create OAuth 2.0 Credentials:**
   - Go to the "Credentials" page in the Google Cloud Console.
   - Click "Create Credentials" and select "OAuth client ID".
   - Choose "Desktop app" as the application type.
   - Download the JSON file and save it as `credentials.json` in the root of the project.

When you run the script with the `--gmail` flag for the first time, you will be prompted to authorize the application.

## IMAP Server Setup

To use the IMAP integration, you need to enable the feature flag and provide the server address and credentials.

### Enabling IMAP

The IMAP feature is controlled by the `enable_imap` feature flag. You can enable it by setting the `DAP_ENABLE_IMAP` environment variable to `true`:

```sh
export DAP_ENABLE_IMAP=true
```

Alternatively, you can set `enable_imap = true` in your configuration file.

### Password Authentication

If your IMAP server uses password authentication, you can provide your credentials using the `--imap-user` and `--imap-password` arguments:

```sh
digital-asset-harvester --imap \
  --imap-server imap.example.com \
  --imap-user user@example.com \
  --imap-password your_password \
  --output crypto_purchases.csv
```

### Gmail (OAuth2)

If you're using Gmail, you'll need to use OAuth2. First, follow the instructions in the "Gmail API Setup" section to get your `credentials.json` file. Then, you can run the script with the `--imap-auth-type gmail_oauth2` argument:

```sh
digital-asset-harvester --imap \
  --imap-server imap.gmail.com \
  --imap-user user@gmail.com \
  --imap-auth-type gmail_oauth2 \
  --output crypto_purchases.csv
```

### Outlook (OAuth2)

If you're using Outlook, you'll need to use OAuth2. First, you'll need to register an application in the Azure portal and get a client ID and authority URL. Then, you can run the script with the `--imap-auth-type outlook_oauth2` argument:

```sh
digital-asset-harvester --imap \
  --imap-server outlook.office365.com \
  --imap-user user@outlook.com \
  --imap-auth-type outlook_oauth2 \
  --client-id your_client_id \
  --authority https://login.microsoftonline.com/your_tenant_id \
  --output crypto_purchases.csv
```

### Direct Ingestion via APIs

In addition to mbox files and IMAP, the harvester supports direct ingestion using Gmail and Outlook APIs. This is often faster and more convenient than downloading large mbox files.

#### Gmail API

Follow the "Gmail API Setup" section to get your `credentials.json`. Then run:

```sh
digital-asset-harvester --gmail --output crypto_purchases.csv
```

You can customize the search query with `--gmail-query` (default: `from:coinbase OR from:binance`).

#### Outlook API (Microsoft Graph)

To use the Outlook API, you'll need to register an application in the Azure portal and get a client ID and authority URL. Then, you can run the script with the `--outlook` flag:

```sh
digital-asset-harvester --outlook \
  --client-id your_client_id \
  --authority https://login.microsoftonline.com/your_tenant_id \
  --output crypto_purchases.csv
```

You can customize the search query with `--outlook-query` (default: `from:coinbase OR from:binance`).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
