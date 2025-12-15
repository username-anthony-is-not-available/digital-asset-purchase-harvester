@echo off
REM Setup script for Windows Command Prompt
REM This script creates a virtual environment and installs dependencies

echo 🚀 Setting up Digital Asset Purchase Harvester...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.7 or higher.
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found
echo 📦 Creating virtual environment...
python -m venv venv

echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

echo 📋 Installing requirements...
pip install -r requirements.txt

echo 🤖 Checking for Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Ollama is not installed. Please install Ollama and pull the required model:
    echo    Visit: https://ollama.ai/download
    echo    Then run: ollama pull llama3.2:3b
) else (
    echo ✅ Ollama found. Make sure you have the required model:
    echo    ollama pull llama3.2:3b
)

echo.
echo ✅ Setup complete!
echo.
echo To get started:
echo 1. Activate the virtual environment: venv\Scripts\activate.bat
echo 2. Run the test script: python test_improvements.py
echo 3. Process your mbox file: python main.py your_file.mbox --output output.csv
echo.
echo To deactivate the virtual environment later: deactivate
pause
