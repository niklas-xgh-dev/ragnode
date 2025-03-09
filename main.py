from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import gradio as gr
import os
import asyncio
import signal
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

# Create a global variable to hold all Gradio apps
gradio_apps = []

# Create separate interfaces for each bot
diamond_hands_interface = ChatInterface(bot_type="diamond-hands").create_interface()
gradio_apps.append(diamond_hands_interface)

aoe2_wizard_interface = ChatInterface(bot_type="aoe2-wizard").create_interface()
gradio_apps.append(aoe2_wizard_interface)

badener_interface = ChatInterface(bot_type="badener").create_interface()
gradio_apps.append(badener_interface)

# Mount each interface
app = gr.mount_gradio_app(app, diamond_hands_interface, path="/diamond-hands/")
app = gr.mount_gradio_app(app, aoe2_wizard_interface, path="/aoe2-wizard/")
app = gr.mount_gradio_app(app, badener_interface, path="/badener/")

# Bot configurations
bots = {
    "diamond-hands": {
        "title": "Diamond Hands",
        "description": "Apes together stronk. Cools you down and doesn't let you YOLO stockpick. Based ETF recommendations.",
        "chat_path": "/diamond-hands/"
    },
    "aoe2-wizard": {
        "title": "AoE2 Wizard",
        "description": "Your Age of Empires II strategy advisor. Get civilization recommendations, build orders, and counter strategies.",
        "chat_path": "/aoe2-wizard/"
    },
    "badener": {
        "title": "The Badener",
        "description": "Complete Baden fanboy, but at least knows everything there is about Baden.",
        "chat_path": "/badener/"
    }
}

# Add shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down server and closing all Gradio connections...")
    for gradio_app in gradio_apps:
        # Close all running Gradio apps
        if hasattr(gradio_app, 'close'):
            await gradio_app.close()
        elif hasattr(gradio_app, '_queue'):
            # For newer Gradio versions
            if hasattr(gradio_app._queue, 'close'):
                await gradio_app._queue.close()
    
    # Give a small timeout to allow connections to close
    await asyncio.sleep(0.5)
    print("Server shutdown complete")

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("unified-template.html", {
        "request": request,
        "page": "home",
        "title": "Home"
    })

@app.get("/{bot_type}-chat", response_class=HTMLResponse)
async def chat_page(request: Request, bot_type: str):
    if bot_type not in bots:
        return templates.TemplateResponse("unified-template.html", {
            "request": request,
            "page": "home",
            "title": "Home - Page Not Found"
        })
    
    bot_config = bots[bot_type]
    return templates.TemplateResponse("unified-template.html", {
        "request": request,
        "page": bot_type,
        "title": bot_config["title"],
        "description": bot_config["description"],
        "chat_path": bot_config["chat_path"]
    })

app.mount("/static", StaticFiles(directory="app/static"), name="static")