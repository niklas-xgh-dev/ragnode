from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import gradio as gr
import os
from dotenv import load_dotenv
from app.backend.database import engine
from app.backend.models import Base

# Load environment variables
if not os.getenv("ANTHROPIC_API_KEY"):
    load_dotenv()

# Import after environment is loaded
from app.backend.chat.interface import ChatInterface

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Create chat interface
chat_interface = ChatInterface().create_interface()

# Mount Gradio app and static files
app = gr.mount_gradio_app(app, chat_interface, path="/chat/")
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")