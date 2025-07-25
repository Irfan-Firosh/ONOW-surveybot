#!/bin/bash

# ONOW Survey Bot API Deployment Script
# Usage: ./deploy.sh [dev|prod]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment is provided
ENVIRONMENT=${1:-dev}

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    print_error "Invalid environment. Use 'dev' or 'prod'"
    exit 1
fi

print_status "Deploying ONOW Survey Bot API in $ENVIRONMENT mode..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data

# Check for environment file
if [[ "$ENVIRONMENT" == "prod" ]]; then
    if [[ ! -f ".env.prod" ]]; then
        print_warning ".env.prod file not found. Creating from .env..."
        if [[ -f ".env" ]]; then
            cp .env .env.prod
        else
            print_error "No .env file found. Please create one with your environment variables."
            exit 1
        fi
    fi
    COMPOSE_FILE="docker-compose.prod.yml"
else
    if [[ ! -f ".env" ]]; then
        print_error "No .env file found. Please create one with your environment variables."
        exit 1
    fi
    COMPOSE_FILE="docker-compose.yml"
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans || true

# Remove old images (optional)
read -p "Do you want to remove old images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Removing old images..."
    docker-compose -f $COMPOSE_FILE down --rmi all --volumes --remove-orphans || true
fi

# Build and start containers
print_status "Building and starting containers..."
docker-compose -f $COMPOSE_FILE up --build -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check if services are running
print_status "Checking service status..."
if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
    print_success "Services are running!"
else
    print_error "Some services failed to start. Check logs with: docker-compose -f $COMPOSE_FILE logs"
    exit 1
fi

# Health check
print_status "Performing health check..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Health check passed!"
        break
    fi
    if [[ $i -eq 30 ]]; then
        print_error "Health check failed after 30 attempts"
        exit 1
    fi
    sleep 2
done

# Show service information
print_status "Service Information:"
echo "API URL: http://localhost:8000"
echo "Health Check: http://localhost:8000/health"
echo "API Documentation: http://localhost:8000/docs"

if [[ "$ENVIRONMENT" == "prod" ]]; then
    echo "Nginx URL: http://localhost:80 (HTTP)"
    echo "Nginx URL: https://localhost:443 (HTTPS - requires SSL certificates)"
fi

# Show logs
print_status "Recent logs:"
docker-compose -f $COMPOSE_FILE logs --tail=20

print_success "Deployment completed successfully!"
print_status "Useful commands:"
echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  Restart services: docker-compose -f $COMPOSE_FILE restart"
echo "  Update services: docker-compose -f $COMPOSE_FILE pull && docker-compose -f $COMPOSE_FILE up -d" 