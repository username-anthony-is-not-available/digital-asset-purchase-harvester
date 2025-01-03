# Digital Asset Purchase Harvester

A Python tool to extract cryptocurrency purchase information from email data stored in mbox files. This project aims to help crypto enthusiasts quickly parse their email history for purchase records.

## ⚠️ Important Notes

- This is a helper tool, not a production-ready solution
- Results may be incomplete or inaccurate - always verify the data
- The project is not actively maintained
- Uses local LLM (Ollama) for basic email parsing

## Features

- Extracts email data from mbox files
- Identifies cryptocurrency purchase emails
- Extracts purchase details such as amount, currency, vendor, and date
- Outputs the extracted data to a CSV file

## Requirements

- Python 3.7+
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/digital-asset-purchase-harvester.git
   cd digital-asset-purchase-harvester
   ```

2. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. Run the script with the path to your mbox file:

   ```sh
   python main.py path/to/your.mbox --output path/to/output.csv
   ```

2. The script will process the mbox file and output the purchase data to the specified CSV file.

## Configuration

- The LLM model used for email parsing can be configured in `config.py`:

  ```python
  LLM_MODEL_NAME = "llama3.2:3b"
  ```

## Example

```sh
python main.py example.mbox --output output/purchase_data.csv
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
