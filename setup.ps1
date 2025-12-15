# Setup script for Windows PowerShell
# This script creates a virtual environment and installs dependencies

Write-Host "Setting up Digital Asset Purchase Harvester..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    if (-not $pythonVersion) {
        throw "Python not found"
    }
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.7 or higher." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Cyan
pip install -r requirements.txt

# Check if Ollama is available
Write-Host "Checking for Ollama..." -ForegroundColor Cyan
try {
    $ollamaVersion = ollama --version 2>$null
    if ($ollamaVersion) {
        Write-Host "Ollama found: $ollamaVersion" -ForegroundColor Green
        Write-Host "Make sure you have the required model: ollama pull llama3.2:3b" -ForegroundColor Yellow
    }
    else {
        throw "Ollama not found"
    }
}
catch {
    Write-Host "Ollama is not installed. Please install Ollama and pull the required model:" -ForegroundColor Yellow
    Write-Host "Visit: https://ollama.ai/download" -ForegroundColor Blue
    Write-Host "Then run: ollama pull llama3.2:3b" -ForegroundColor Blue
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To get started:" -ForegroundColor Cyan
Write-Host "1. Activate the virtual environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Run the test script: python test_improvements.py" -ForegroundColor White
Write-Host "3. Process your mbox file: python main.py your_file.mbox --output output.csv" -ForegroundColor White
Write-Host ""
Write-Host "To deactivate the virtual environment later: deactivate" -ForegroundColor Yellow
