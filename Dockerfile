FROM python:3.13-slim AS backend

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Set up NodeJS for Svelte
FROM node:22-slim AS builder

WORKDIR /app

# Copy Svelte app files
COPY app/svelte ./svelte

WORKDIR /app/svelte

# Install dependencies and build
RUN npm install
RUN npm run build

# Final image
FROM python:3.13-slim

WORKDIR /app

# Copy requirements and install directly in the final image
COPY requirements.txt .
RUN pip install -r requirements.txt

# Create directory structure for static files
RUN mkdir -p app/static/dist

# Copy the built Svelte files
COPY --from=builder /app/svelte/dist/ ./app/static/dist/

# Copy the rest of the application code
COPY . .

# Ensure permissions are set correctly
RUN chmod -R 755 /app/app/static

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]