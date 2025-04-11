#!/bin/bash
set -e

echo "Starting development environment with Docker Compose..."

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Warning: .env file not found. Creating an empty one..."
  touch .env
fi

# Ensure bots config directory exists
mkdir -p app/config/bots app/knowledge

# Stop and remove existing containers if they exist
echo "Cleaning up any existing containers..."
docker-compose down 2>/dev/null || true

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
  echo "docker-compose not found. Trying with 'docker compose'..."
  # Try with docker compose
  if ! command -v docker &> /dev/null; then
    echo "Error: docker not found. Please install Docker first."
    exit 1
  fi
  
  # Run with docker compose with logs
  echo "Starting containers with docker compose..."
  docker compose up --build
else
  # Run with docker-compose
  echo "Starting containers with docker-compose..."
  docker-compose up --build
fi