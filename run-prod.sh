#!/bin/bash
set -e

echo "Building production container..."

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Warning: .env file not found. Creating an empty one..."
  touch .env
fi

# Build production image
docker build -t ragnode-prod -f Dockerfile.prod .

# Run the container
docker run -p 8000:8000 --env-file .env ragnode-prod