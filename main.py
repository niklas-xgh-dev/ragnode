from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import gradio as gr
import os
from dotenv import load_dotenv

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

# Configure templates
templates = Jinja2Templates(directory="app/static")

# Create a single chat interface that we'll reuse
# Later we can modify ChatInterface to handle different environments
chat_interface = ChatInterface().create_interface()

# Mount the same Gradio app at different paths
app = gr.mount_gradio_app(app, chat_interface, path="/chat/")
app = gr.mount_gradio_app(app, chat_interface, path="/diamond-hands/")
app = gr.mount_gradio_app(app, chat_interface, path="/chippie/")
app = gr.mount_gradio_app(app, chat_interface, path="/badener/")

# Define routes for HTML pages
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/diamond-hands-chat", response_class=HTMLResponse)
async def diamond_hands_page(request: Request):
    return templates.TemplateResponse("chat-template.html", {
        "request": request,
        "title": "Diamond Hands",
        "description": "Apes together stronk. Cools you down and doesn't let you YOLO stockpick. Based ETF recommendations.",
        "chat_path": "/diamond-hands/"
    })

@app.get("/chippie-chat", response_class=HTMLResponse)
async def chippie_page(request: Request):
    return templates.TemplateResponse("chat-template.html", {
        "request": request,
        "title": "Chippie",
        "description": "Semiconductor nerd. Takes one to like one.",
        "chat_path": "/chippie/"
    })

@app.get("/badener-chat", response_class=HTMLResponse)
async def badener_page(request: Request):
    return templates.TemplateResponse("chat-template.html", {
        "request": request,
        "title": "The Badener",
        "description": "Complete Baden fanboy, but at least knows everything there is about Baden.",
        "chat_path": "/badener/"
    })

# Mount static files last to not override routes
app.mount("/static", StaticFiles(directory="app/static"), name="static")