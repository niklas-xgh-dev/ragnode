FROM python:3.12-slim as backend

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Set up NodeJS for Svelte
FROM node:18-slim as frontend

WORKDIR /app/svelte

COPY app/svelte/package.json app/svelte/package-lock.json* ./
RUN npm install

COPY app/svelte .
RUN npm run build

# Final image
FROM python:3.12-slim

WORKDIR /app

# Copy Python dependencies from backend stage
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy built frontend
COPY --from=frontend /app/static/dist /app/static/dist

# Copy application code
COPY . .

RUN chmod -R 755 /app/app/static

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]