#!/bin/bash
set -e

echo "Building Svelte frontend..."
(cd app/svelte && npm install && npm run build)

echo "Creating dist directory if it doesn't exist..."
mkdir -p app/static/dist

echo "Copying built frontend to static directory..."
cp -r app/svelte/dist/* app/static/dist/

echo "Building Docker image..."
docker build -t ragnode .

echo "Running Docker container..."
docker run -p 8000:8000 --env-file .env ragnode