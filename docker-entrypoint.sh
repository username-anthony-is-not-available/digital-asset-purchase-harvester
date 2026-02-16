#!/bin/bash
# Digital Asset Purchase Harvester - Docker Entrypoint Script
set -e

# Function to start Ollama server in the background
start_ollama() {
    echo "Starting Ollama server in background..."
    # Start ollama and redirect its output to a log file
    ollama serve > /app/ollama.log 2>&1 &

    # Wait for Ollama to be ready (up to 60 seconds)
    local retries=0
    local max_retries=60
    until curl -s http://localhost:11434/api/tags > /dev/null || [ $retries -eq $max_retries ]; do
        echo "Waiting for Ollama to start... ($retries/$max_retries)"
        sleep 1
        ((retries++))
    done

    if [ $retries -eq $max_retries ]; then
        echo "❌ Ollama failed to start within $max_retries seconds"
        # Print logs to help debugging
        cat /app/ollama.log
        exit 1
    fi
    echo "✅ Ollama is ready."
}

# Check if we should start local Ollama
# We start it if OLLAMA_HOST is targeting localhost/127.0.0.1
# AND if the command is not 'ollama serve' itself (to avoid port conflicts)
if [[ "$OLLAMA_HOST" == *"localhost"* ]] || [[ "$OLLAMA_HOST" == *"127.0.0.1"* ]]; then
    if [[ "$1" == *"ollama"* ]] && [[ "$2" == "serve" ]]; then
        echo "Ollama serve detected in command, skipping background startup."
    else
        start_ollama
    fi
fi

# Execute the main command
exec "$@"
