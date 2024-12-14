from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app=FastAPI()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy app v1.007"}

app.mount("/", StaticFiles(directory="../frontend", html=True))