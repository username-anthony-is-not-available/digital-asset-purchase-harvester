# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using the Digital Asset Purchase Harvester.

---

## Common Issues

### 1. Ollama Connection Errors

**Symptoms:**

```
Error: Connection refused to localhost:11434
Error: LLM network error: [Errno 111] Connection refused
```

**Solutions:**

1. **Check if Ollama is running:**

   ```bash
   # Check if Ollama process is running
   ps aux | grep ollama  # Linux/macOS
   tasklist | findstr ollama  # Windows
   ```

2. **Start Ollama:**

   ```bash
   ollama serve
   ```

3. **Verify Ollama is accessible:**

   ```bash
   curl http://localhost:11434/api/tags
   ```

4. **Check custom Ollama host:**
   If you're using a custom Ollama host, set the environment variable:
   ```bash
   export OLLAMA_HOST=http://your-host:11434  # Linux/macOS
   set OLLAMA_HOST=http://your-host:11434     # Windows CMD
   $env:OLLAMA_HOST="http://your-host:11434"  # Windows PowerShell
   ```

---

### 2. Model Not Found

**Symptoms:**

```
Error: model 'llama3.2:3b' not found
```

**Solutions:**

1. **Pull the required model:**

   ```bash
   ollama pull llama3.2:3b
   ```

2. **List installed models:**

   ```bash
   ollama list
   ```

3. **Use a different model:**
   Set the `DAP_LLM_MODEL_NAME` environment variable:
   ```bash
   export DAP_LLM_MODEL_NAME=gemma3:4b  # Linux/macOS
   set DAP_LLM_MODEL_NAME=gemma3:4b     # Windows CMD
   $env:DAP_LLM_MODEL_NAME="gemma3:4b"  # Windows PowerShell
   ```

---

### 3. Low Detection Rate

**Symptoms:**

- Few or no purchases detected despite knowing purchase emails exist in the mailbox
- Many "non-purchase emails" in the metrics

**Diagnostic Steps:**

1. **Enable debug logging:**

   ```bash
   export DAP_LOG_LEVEL=DEBUG
   export DAP_ENABLE_DEBUG_OUTPUT=true
   digital-asset-harvester your.mbox --output output.csv
   ```

2. **Check preprocessing filtering:**
   The tool pre-filters emails to reduce LLM calls. You might be filtering out valid purchases.

   **Disable preprocessing temporarily:**

   ```bash
   export DAP_ENABLE_PREPROCESSING=false
   digital-asset-harvester your.mbox --output output.csv
   ```

3. **Review confidence threshold:**
   Lower the confidence threshold to catch more borderline cases:

   ```bash
   export DAP_MIN_CONFIDENCE_THRESHOLD=0.4
   digital-asset-harvester your.mbox --output output.csv
   ```

4. **Check supported exchanges:**
   Review the list of supported exchanges in the README. If your exchange isn't listed, the keyword detection may fail.

---

### 4. Slow Processing Speed

**Symptoms:**

- Processing takes much longer than expected
- Progress bar moves very slowly

**Diagnostic Steps:**

1. **Check LLM response time:**
   Enable debug logging to see individual LLM call times:

   ```bash
   export DAP_ENABLE_DEBUG_OUTPUT=true
   ```

2. **Optimize LLM settings:**

   - **Use a smaller model:**
     ```bash
     export DAP_LLM_MODEL_NAME=llama3.2:1b
     ```
   - **Reduce timeout:**
     ```bash
     export DAP_LLM_TIMEOUT_SECONDS=15
     ```

3. **Enable preprocessing** (if disabled):
   Preprocessing filters out ~70% of emails before LLM calls:

   ```bash
   export DAP_ENABLE_PREPROCESSING=true
   ```

4. **Hardware considerations:**
   - LLM inference is CPU/GPU intensive
   - Ensure Ollama has sufficient resources
   - Consider closing other applications

**Performance Expectations:**

- With preprocessing: ~100-200 emails/minute
- Without preprocessing: ~30-50 emails/minute
- Varies based on: hardware, model size, email length

---

### 5. Memory Issues with Large Mailboxes

**Symptoms:**

```
MemoryError: Unable to allocate array
Process killed (OOM)
```

**Solutions:**

1. **Split large mbox files:**

   ```bash
   # Linux/macOS with GNU split
   split -l 10000 large.mbox small_mbox_

   # Process each chunk
   for file in small_mbox_*; do
     digital-asset-harvester "$file" --output "output_${file}.csv"
   done
   ```

2. **Reduce batch size:**

   ```bash
   export DAP_BATCH_SIZE=5
   ```

3. **Monitor memory usage:**

   ```bash
   # Linux/macOS
   watch -n 1 'ps aux | grep python'

   # Windows PowerShell
   while($true) { Get-Process python | Select-Object CPU,PM,WS; Start-Sleep 1; Clear-Host }
   ```

---

### 6. Validation Errors

**Symptoms:**

```
Validation error: currency must be ISO 4217 uppercase code
Validation error: amount must be greater than zero
```

**Diagnostic Steps:**

1. **Review extracted data:**
   Check the output CSV to see what was actually extracted

2. **Disable strict validation:**

   ```bash
   export DAP_STRICT_VALIDATION=false
   digital-asset-harvester your.mbox --output output.csv
   ```

3. **Allow unknown cryptocurrencies:**

   ```bash
   export DAP_ALLOW_UNKNOWN_CRYPTOS=true
   ```

4. **Inspect LLM responses:**
   Enable debug output to see raw LLM extraction:
   ```bash
   export DAP_ENABLE_DEBUG_OUTPUT=true
   ```

---

### 7. Import Errors

**Symptoms:**

```
ModuleNotFoundError: No module named 'digital_asset_harvester'
ImportError: cannot import name 'EmailPurchaseExtractor'
```

**Solutions:**

1. **Check virtual environment is activated:**
   You should see `(venv)` in your terminal prompt.

   **Activate:**

   ```bash
   # Linux/macOS
   source venv/bin/activate

   # Windows PowerShell
   .\venv\Scripts\Activate.ps1

   # Windows CMD
   venv\Scripts\activate.bat
   ```

2. **Reinstall dependencies:**

   ```bash
   pip install --force-reinstall -r requirements.txt
   ```

3. **Install in editable mode:**

   ```bash
   pip install -e .
   ```

4. **Check Python path:**
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```

---

## Debugging Techniques

### Enable Maximum Logging

```bash
export DAP_LOG_LEVEL=DEBUG
export DAP_ENABLE_DEBUG_OUTPUT=true
export DAP_LOG_JSON_OUTPUT=false  # Human-readable logs

digital-asset-harvester your.mbox --output output.csv 2>&1 | tee debug.log
```

### Test with Sample Emails

Create a small test mbox with 2-3 known purchase emails to validate the setup:

```python
import mailbox

# Create test mbox
mbox = mailbox.mbox('test.mbox')
msg = mailbox.mboxMessage()
msg['Subject'] = 'Your Coinbase Purchase'
msg['From'] = 'noreply@coinbase.com'
msg['Date'] = '2024-01-15 10:00:00'
msg.set_payload('''
You bought 0.5 BTC for $15,000.00 USD.
Transaction ID: ABC123
Date: January 15, 2024
''')
mbox.add(msg)
mbox.close()
```

Then run:

```bash
digital-asset-harvester test.mbox --output test_output.csv
```

### Check Individual Components

Test components separately:

```python
from digital_asset_harvester import get_settings, OllamaLLMClient

# Test settings
settings = get_settings()
print(settings)

# Test LLM client
llm = OllamaLLMClient(settings=settings)
result = llm.generate_json("Return JSON: {\"test\": true}")
print(result.data)
```

---

## Performance Optimization

### 1. Use Preprocessing

Ensure preprocessing is enabled (default):

```bash
export DAP_ENABLE_PREPROCESSING=true
```

### 2. Reduce Retries

If network is stable, reduce retry attempts:

```bash
export DAP_LLM_MAX_RETRIES=1
```

### 3. Smaller Model

Switch to a faster, smaller model:

```bash
export DAP_LLM_MODEL_NAME=llama3.2:1b
```

### 4. Disable Progress Bar

For batch processing, disable progress bar to reduce overhead:

```bash
digital-asset-harvester your.mbox --output output.csv --no-progress
```

---

## Getting Help

If you're still stuck:

1. **Check GitHub Issues:** Someone may have encountered the same problem

   - https://github.com/username-anthony-is-not-available/digital-asset-purchase-harvester/issues

2. **Create a debug log:**

   ```bash
   export DAP_ENABLE_DEBUG_OUTPUT=true
   digital-asset-harvester your.mbox --output output.csv 2>&1 | tee debug.log
   ```

   Include relevant excerpts in your issue report.

3. **Provide context:**
   - OS and Python version: `python --version`
   - Ollama version: `ollama --version`
   - Package version: `pip show digital-asset-purchase-harvester`
   - Number of emails in mailbox
   - Sample (anonymized) email that failed

---

## Frequently Asked Questions

### Why are some legitimate purchases not detected?

**Reasons:**

1. **Unknown exchange:** The exchange isn't in our keyword list
2. **Unusual email format:** The email structure differs from training examples
3. **Confidence too low:** Extraction succeeded but confidence < threshold
4. **Preprocessing filtered it out:** Email didn't match crypto/purchase keywords

**Solutions:**

- Add exchange keywords to your fork
- Lower confidence threshold
- Disable preprocessing temporarily
- Manually review filtered emails in debug logs

### Can I process Gmail directly without downloading mbox?

Not currently. You must:

1. Use Gmail Takeout to export emails as mbox
2. Or use a tool like `getmail` or `fetchmail`

### Why is the output incomplete or inaccurate?

**This is a best-effort tool using LLMs, which are probabilistic:**

- Always verify the results
- Use confidence scores to identify uncertain extractions
- Cross-reference with your actual exchange records

### How do I improve accuracy?

1. **Use a larger model** (e.g., `llama3:7b` instead of `llama3.2:3b`)
2. **Customize prompts** (advanced users)
3. **Train on your specific exchanges** (requires code modification)

### Can I run this without internet?

**Yes!** Ollama runs locally. No data is sent to external services.

---

## System Requirements

**Minimum:**

- Python 3.9+
- 4 GB RAM
- 10 GB disk space (for Ollama models)

**Recommended:**

- Python 3.11+
- 8 GB RAM
- SSD storage
- Multi-core CPU (for faster LLM inference)

---

## Configuration Reference

See [README.md](README.md#configuration) for full configuration options.

**Quick reference:**

- `DAP_LLM_MODEL_NAME`: Model to use (default: `llama3.2:3b`)
- `DAP_LLM_MAX_RETRIES`: Retry attempts for LLM calls (default: `3`)
- `DAP_ENABLE_PREPROCESSING`: Filter emails before LLM (default: `true`)
- `DAP_MIN_CONFIDENCE_THRESHOLD`: Minimum confidence to accept (default: `0.6`)
- `DAP_LOG_LEVEL`: Logging verbosity (default: `INFO`)
