# Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Copy Svelte app files
COPY app/svelte ./svelte

WORKDIR /build/svelte

# Install dependencies and build
RUN npm install
RUN npm run build

# Build backend
FROM python:3.11-slim

WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure
RUN mkdir -p app/static/dist app/config/bots app/knowledge

# Copy all application files excluding svelte directory
COPY main.py ./
COPY app/*.py ./app/
COPY app/config ./app/config/
COPY app/knowledge ./app/knowledge/
COPY app/static ./app/static/

# Copy built frontend from the builder stage
COPY --from=frontend-builder /build/svelte/dist/ ./app/static/dist/

# Set correct permissions
RUN chmod -R 755 /app/app/static

# Check if the files are in the right place
RUN ls -la /app/app/static/dist

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application with proper settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]