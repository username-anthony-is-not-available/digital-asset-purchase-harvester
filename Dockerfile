# Digital Asset Purchase Harvester - Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Install package in editable mode
RUN pip install -e .

# Create directory for output
RUN mkdir -p /app/output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DAP_LOG_LEVEL=INFO

# Expose port for web interface if needed
EXPOSE 8000

# Default command
CMD ["digital-asset-harvester", "--help"]
