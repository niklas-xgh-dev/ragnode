from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import gradio as gr
import os
from dotenv import load_dotenv

if not os.getenv("ANTHROPIC_API_KEY"):
    load_dotenv()

from app.backend.chat.interface import ChatInterface

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/static")

# Create separate interfaces for each bot
diamond_hands_interface = ChatInterface(bot_type="diamond-hands").create_interface()
chippie_interface = ChatInterface(bot_type="chippie").create_interface()
badener_interface = ChatInterface(bot_type="badener").create_interface()

# Mount each interface
app = gr.mount_gradio_app(app, diamond_hands_interface, path="/diamond-hands/")
app = gr.mount_gradio_app(app, chippie_interface, path="/chippie/")
app = gr.mount_gradio_app(app, badener_interface, path="/badener/")

# Routes remain the same
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

app.mount("/static", StaticFiles(directory="app/static"), name="static")