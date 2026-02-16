#!/bin/bash
# Digital Asset Purchase Harvester - Docker Setup Script
# ========================================================
# This script automates the Docker environment setup for the project.
# It is designed to work on Linux/macOS and requires bash to be installed.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE_NAME="digital-asset-harvester"
OLLAMA_MODEL="llama3.2:3b"

# Helper functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Docker installation
check_docker() {
    print_header "Checking Docker Installation"
    
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version)
        print_success "Docker is installed: $DOCKER_VERSION"
        
        # Check if Docker daemon is running
        if docker ps >/dev/null 2>&1; then
            print_success "Docker daemon is running"
        else
            print_error "Docker daemon is not running"
            print_info "Please start Docker and try again"
            exit 1
        fi
    else
        print_warning "Docker is not installed"
        print_info "Installing Docker..."
        
        # Install Docker based on OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
            sudo sh /tmp/get-docker.sh
            sudo usermod -aG docker "$USER"
            rm /tmp/get-docker.sh
            print_success "Docker installed successfully"
            print_warning "Please log out and back in for group changes to take effect"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            print_error "Please install Docker Desktop for Mac from: https://www.docker.com/products/docker-desktop"
            exit 1
        else
            print_error "Unsupported operating system"
            exit 1
        fi
    fi
}

# Check Docker Compose installation
check_docker_compose() {
    print_header "Checking Docker Compose Installation"
    
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_VERSION=$(docker compose version)
        print_success "Docker Compose is installed: $COMPOSE_VERSION"
    else
        print_warning "Docker Compose is not installed"
        print_info "Docker Compose is typically included with Docker Desktop"
        print_info "For Linux, you may need to install it separately"
        exit 1
    fi
}

# Build Docker image
build_docker_image() {
    print_header "Building Docker Image"
    
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in the current directory"
        print_info "Creating a basic Dockerfile..."
        create_dockerfile
    fi
    
    print_info "Building image: $DOCKER_IMAGE_NAME"
    docker build --build-arg OLLAMA_MODEL="$OLLAMA_MODEL" -t "$DOCKER_IMAGE_NAME:latest" .
    print_success "Docker image built successfully"
}

# Create Dockerfile if it doesn't exist
create_dockerfile() {
    cat > Dockerfile <<'EOF'
# Digital Asset Purchase Harvester - Multi-stage Dockerfile
# Stage 1: Model Cache
FROM ollama/ollama:latest AS model-cache
ARG OLLAMA_MODEL=llama3.2:3b
RUN ollama serve & sleep 5 && ollama pull ${OLLAMA_MODEL}

# Stage 2: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN pip install --no-cache-dir .

# Stage 3: Final
FROM python:3.11-slim AS final
WORKDIR /app
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*
RUN curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/bin/ollama && chmod +x /usr/bin/ollama
COPY --from=model-cache /root/.ollama /root/.ollama
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
ENV PYTHONUNBUFFERED=1
ENV DAP_LOG_LEVEL=INFO
ENV OLLAMA_HOST=http://localhost:11434
RUN mkdir -p /app/output
EXPOSE 8000 11434
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["digital-asset-harvester", "--help"]
EOF
    print_success "Dockerfile created"
}

# Create docker-compose.yml if it doesn't exist
create_docker_compose() {
    print_header "Checking Docker Compose Configuration"
    
    if [ ! -f "docker-compose.yml" ]; then
        print_info "Creating docker-compose.yml..."
        cat > docker-compose.yml <<'EOF'
services:
  harvester:
    build: .
    image: digital-asset-harvester:latest
    container_name: digital-asset-harvester
    volumes:
      - ./:/app
      - ./output:/app/output
    environment:
      - DAP_LOG_LEVEL=${DAP_LOG_LEVEL:-INFO}
      - DAP_LLM_MODEL_NAME=${DAP_LLM_MODEL_NAME:-llama3.2:3b}
      - DAP_ENABLE_CLOUD_LLM=${DAP_ENABLE_CLOUD_LLM:-false}
      - OLLAMA_HOST=${OLLAMA_HOST:-http://ollama:11434}
    depends_on:
      - ollama
    networks:
      - harvester-network
    command: ["tail", "-f", "/dev/null"]  # Keep container running

  ollama:
    build: .
    image: digital-asset-harvester:latest
    container_name: ollama-service
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - harvester-network
    command: ["ollama", "serve"]

networks:
  harvester-network:
    driver: bridge

volumes:
  ollama-data:
EOF
        print_success "docker-compose.yml created"
    else
        print_info "docker-compose.yml already exists"
    fi
}

# Create docker-entrypoint.sh if it doesn't exist
create_entrypoint() {
    if [ ! -f "docker-entrypoint.sh" ]; then
        print_info "Creating docker-entrypoint.sh..."
        cat > docker-entrypoint.sh <<'EOF'
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
EOF
        chmod +x docker-entrypoint.sh
        print_success "docker-entrypoint.sh created"
    fi
}

# Create .dockerignore if it doesn't exist
create_dockerignore() {
    if [ ! -f ".dockerignore" ]; then
        print_info "Creating .dockerignore..."
        cat > .dockerignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.benchmarks/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Build artifacts
build/
dist/
*.egg-info/

# Documentation
docs/_build/

# Credentials and configs
credentials.json
token.json
*.mbox
*.csv
tmpcfg.toml

# Temporary files
tmp/
temp/
*.tmp
EOF
        print_success ".dockerignore created"
    fi
}

# Setup Ollama model
setup_ollama_model() {
    print_header "Setting up Ollama Model"
    
    print_info "The Docker image now includes pre-cached model weights for $OLLAMA_MODEL."
    print_info "Starting Ollama service..."
    docker compose up -d ollama
    
    # Wait for Ollama to be ready
    print_info "Waiting for Ollama service to be ready..."
    sleep 5
    
    # Verify the model is present
    print_info "Verifying model availability..."
    if docker compose exec -T ollama ollama list | grep -q "$(echo $OLLAMA_MODEL | cut -d: -f1)"; then
        print_success "Verified $OLLAMA_MODEL is available (pre-cached or already pulled)."
    else
        print_warning "Model $OLLAMA_MODEL not found in image, pulling now..."
        docker compose exec -T ollama ollama pull "$OLLAMA_MODEL" || {
            print_warning "Failed to pull model automatically"
            print_info "You can pull it manually later with: docker compose exec ollama ollama pull $OLLAMA_MODEL"
        }
    fi
    
    print_success "Ollama setup complete"
}

# Start services
start_services() {
    print_header "Starting Services"
    
    print_info "Starting all services with Docker Compose..."
    docker compose up -d
    
    print_success "All services started successfully"
    print_info "Harvester container: docker compose exec harvester bash"
    print_info "View logs: docker compose logs -f"
}

# Display usage information
show_usage() {
    print_header "Usage Information"
    
    echo ""
    echo "The Docker environment is now set up!"
    echo ""
    echo "Available commands:"
    echo "  docker compose up -d              # Start all services"
    echo "  docker compose down               # Stop all services"
    echo "  docker compose logs -f            # View logs"
    echo "  docker compose exec harvester bash # Access container shell"
    echo ""
    echo "Run the harvester:"
    echo "  docker compose exec harvester digital-asset-harvester --help"
    echo ""
    echo "Example:"
    echo "  docker compose exec harvester digital-asset-harvester \\"
    echo "    --mbox-file /app/your_emails.mbox \\"
    echo "    --output /app/output/crypto_purchases.csv"
    echo ""
    print_info "Make sure to place your .mbox files in the project directory"
    print_info "Output files will be saved to the ./output directory"
}

# Main execution
main() {
    print_header "Digital Asset Purchase Harvester - Docker Setup"
    echo ""
    
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Create necessary files
    create_dockerignore
    create_entrypoint
    create_docker_compose
    
    # Build and setup
    build_docker_image
    setup_ollama_model
    start_services
    
    # Show usage
    show_usage
    
    print_success "Setup completed successfully! 🎉"
}

# Run main function
main
