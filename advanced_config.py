# Advanced Configuration for Digital Asset Purchase Harvester

# LLM Configuration
LLM_MODEL_NAME = "gemma3:4b"
LLM_MAX_RETRIES = 3
LLM_TIMEOUT_SECONDS = 30

# Processing Configuration
ENABLE_PREPROCESSING = True  # Enable keyword-based filtering before LLM
ENABLE_VALIDATION = True  # Enable post-extraction validation
MIN_CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence score to accept results

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
ENABLE_DEBUG_OUTPUT = False  # Enable detailed debug logging for troubleshooting

# Performance Configuration
BATCH_SIZE = 10  # Number of emails to process before logging progress
ENABLE_PARALLEL_PROCESSING = False  # Future feature for parallel processing

# Data Quality Configuration
STRICT_VALIDATION = True  # Require all fields to be present and valid
ALLOW_UNKNOWN_CRYPTOS = True  # Accept cryptocurrencies not in the predefined list
REQUIRE_NUMERIC_VALIDATION = True  # Validate that amounts are reasonable numbers

# Output Configuration
INCLUDE_PROCESSING_METADATA = False  # Include processing notes in CSV output
INCLUDE_CONFIDENCE_SCORES = False  # Include confidence scores in CSV output
