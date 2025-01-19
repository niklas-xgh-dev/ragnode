FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN chmod -R 755 /app/app/static

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]