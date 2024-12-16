FROM python:3.12-slim

ARG ANTHROPIC_API_KEY
ENV ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

WORKDIR /app
COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/backend backend/
COPY app/frontend frontend/

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]