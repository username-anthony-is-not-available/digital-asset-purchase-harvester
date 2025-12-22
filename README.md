# Digital Asset Purchase Harvester

[![CI](https://github.com/username-anthony-is-not-available/digital-asset-purchase-harvester/actions/workflows/ci.yml/badge.svg)](https://github.com/username-anthony-is-not-available/digital-asset-purchase-harvester/actions/workflows/ci.yml)

A Python tool to extract cryptocurrency purchase information from email data stored in mbox files. This project aims to help crypto enthusiasts quickly parse their email history for purchase records.

## ⚠️ Important Notes

- This is a helper tool, not a production-ready solution
- Results may be incomplete or inaccurate - always verify the data
- The project is not actively maintained
- Uses local LLM (Ollama) for email parsing and analysis

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
     _(or run `python -m digital_asset_harvester.cli` if you prefer module execution)_

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

## Project Structure

```
digital_asset_harvester/
├── __init__.py
├── config.py
├── ingest/
│   └── mbox_reader.py
├── output/
│   └── csv_writer.py
├── processing/
│   └── email_purchase_extractor.py
└── utils/
   └── file_utils.py
```

Legacy modules such as `email_purchase_extractor.py` still proxy to the packaged implementation for backwards compatibility, but new development should import from `digital_asset_harvester`.

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
     python main.py --mbox-file path/to/your.mbox --output path/to/output.csv
     ```
   - **Directly from Gmail:**
     ```sh
     python main.py --gmail --output path/to/output.csv
     ```

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
python main.py example.mbox --output output/purchase_data.csv

# The improved system will now:
# 1. Pre-filter emails using keyword detection
# 2. Use enhanced LLM prompts for better accuracy
# 3. Validate extracted data for quality
# 4. Provide detailed processing statistics
```

### advanced_config.py overrides

Advanced defaults can be configured in `advanced_config.py`. Any uppercase variable matching a `HarvesterSettings` field name will override the base configuration:

```python
# LLM Configuration
LLM_MODEL_NAME = "llama3.2:3b"
MIN_CONFIDENCE_THRESHOLD = 0.6

# Processing Configuration
ENABLE_PREPROCESSING = True    # Enable smart filtering
STRICT_VALIDATION = True      # Require all fields to be valid
ENABLE_DEBUG_OUTPUT = False   # Detailed logging for troubleshooting
```

### LLM client customization

`EmailPurchaseExtractor` now depends on `OllamaLLMClient`, which encapsulates retries, timeouts, and JSON parsing. You can provide a customised client (for example, with a different model or temperature) when instantiating the extractor:

```python
from digital_asset_harvester import EmailPurchaseExtractor, OllamaLLMClient, get_settings_with_overrides

settings = get_settings_with_overrides(llm_model_name="gemma3:4b")
llm_client = OllamaLLMClient(settings=settings, default_retries=5)
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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
