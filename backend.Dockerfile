FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure
RUN mkdir -p app/static/dist app/config/bots app/knowledge

# Copy application code
COPY main.py ./
COPY app ./app/

# Make config directory if it doesn't exist
RUN mkdir -p app/config/bots app/knowledge

# Ensure bot configurations are accessible
RUN ls -la /app/app/config

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application with proper settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]