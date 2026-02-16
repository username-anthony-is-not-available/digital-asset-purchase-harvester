# Digital Asset Purchase Harvester - Multi-stage Dockerfile
# ========================================================
# This Dockerfile uses a multi-stage build to:
# 1. Pre-cache the Ollama model weights
# 2. Build the Python application and its dependencies
# 3. Create a lightweight final image with both components

# --- Stage 1: Model Cache ---
# Pre-pull the default model used by the application
FROM ollama/ollama:latest AS model-cache
ARG OLLAMA_MODEL=llama3.2:3b
RUN ollama serve & sleep 5 && ollama pull ${OLLAMA_MODEL}

# --- Stage 2: Python Builder ---
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy source and install the package
COPY . .
RUN pip install --no-cache-dir .

# --- Stage 3: Final Runtime ---
FROM python:3.11-slim AS final
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama binary for local model execution
RUN curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/bin/ollama && \
    chmod +x /usr/bin/ollama

# Copy pre-cached models from Stage 1
COPY --from=model-cache /root/.ollama /root/.ollama

# Copy installed Python packages and scripts from Stage 2
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DAP_LOG_LEVEL=INFO
ENV OLLAMA_HOST=http://localhost:11434

# Create directory for output
RUN mkdir -p /app/output

# Expose ports for Web UI (8000) and Ollama API (11434)
EXPOSE 8000
EXPOSE 11434

# Use the entrypoint script to handle Ollama and the application startup
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["digital-asset-harvester", "--help"]
