docker build -t ragnode .      
docker run -p 8000:8000 --env-file .env ragnode