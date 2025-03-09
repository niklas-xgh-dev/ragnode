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

from app.backend.chat.interface import ChatInterface, get_available_bots

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

# Get all available bots from config files
bots = get_available_bots()

# Create and mount interfaces for each bot
for bot_id, bot_config in bots.items():
    try:
        # Create the interface
        interface = ChatInterface(bot_id=bot_id).create_interface()
        gradio_apps.append(interface)
        
        # Mount the interface
        chat_path = bot_config.get("chat_path", f"/{bot_id}/")
        app = gr.mount_gradio_app(app, interface, path=chat_path)
        
        print(f"Mounted {bot_id} interface at {chat_path}")
        
    except Exception as e:
        print(f"Error mounting interface for {bot_id}: {str(e)}")

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
        "title": "Home",
        "bots": bots
    })

@app.get("/{bot_id}-chat", response_class=HTMLResponse)
async def chat_page(request: Request, bot_id: str):
    if bot_id not in bots:
        return templates.TemplateResponse("unified-template.html", {
            "request": request,
            "page": "home",
            "title": "Home - Page Not Found",
            "bots": bots
        })
    
    bot_config = bots[bot_id]
    return templates.TemplateResponse("unified-template.html", {
        "request": request,
        "page": bot_id,
        "title": bot_config["title"],
        "description": bot_config["description"],
        "chat_path": bot_config["chat_path"],
        "bots": bots
    })

app.mount("/static", StaticFiles(directory="app/static"), name="static")