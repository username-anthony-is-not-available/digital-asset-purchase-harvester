#!/bin/bash
# Setup script for Linux/macOS
# This script creates a virtual environment and installs dependencies

echo "🚀 Setting up Digital Asset Purchase Harvester..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📋 Installing requirements..."
pip install -r requirements.txt

# Check if Ollama is available
echo "🤖 Checking for Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama is not installed. Please install Ollama and pull the required model:"
    echo "   Visit: https://ollama.ai/download"
    echo "   Then run: ollama pull llama3.2:3b"
else
    echo "✅ Ollama found. Make sure you have the required model:"
    echo "   ollama pull llama3.2:3b"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To get started:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the test script: python test_improvements.py"
echo "3. Process your mbox file: python main.py your_file.mbox --output output.csv"
echo ""
echo "To deactivate the virtual environment later: deactivate"
