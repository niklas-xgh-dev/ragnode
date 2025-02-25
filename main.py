from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import gradio as gr
import os
import yaml
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
aoe2_wizard_interface = ChatInterface(bot_type="aoe2-wizard").create_interface()
badener_interface = ChatInterface(bot_type="badener").create_interface()

# Mount each interface
app = gr.mount_gradio_app(app, diamond_hands_interface, path="/diamond-hands/")
app = gr.mount_gradio_app(app, aoe2_wizard_interface, path="/aoe2-wizard/")
app = gr.mount_gradio_app(app, badener_interface, path="/badener/")

# Routes
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

@app.get("/aoe2-wizard-chat", response_class=HTMLResponse)
async def aoe2_wizard_page(request: Request):
    return templates.TemplateResponse("aoe2wizard.html", {
        "request": request,
        "title": "AoE2 Wizard",
        "description": "Your Age of Empires II strategy advisor. Get civilization recommendations, build orders, and counter strategies.",
        "chat_path": "/aoe2-wizard/"
    })

@app.get("/badener-chat", response_class=HTMLResponse)
async def badener_page(request: Request):
    return templates.TemplateResponse("chat-template.html", {
        "request": request,
        "title": "The Badener",
        "description": "Complete Baden fanboy, but at least knows everything there is about Baden.",
        "chat_path": "/badener/"
    })

# Hidden route for AoE2 civilizations (accessible but not in nav)
@app.get("/aoe2-civs", response_class=HTMLResponse)
async def aoe2_civs_page(request: Request):
    # Load YAML file
    yaml_path = "app/knowledge/aoe2civs.yaml"
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Get civilizations and pre-sort them by tier
    civilizations = data.get("civilizations", [])
    
    # Custom sorting function for tiers
    def tier_sort_key(civ):
        tier = civ.get('tier', 'Z')  # Default to Z for unknown tiers
        tier_order = {'S': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5}
        return tier_order.get(tier, 999)
    
    # Sort civilizations by tier
    sorted_civilizations = sorted(civilizations, key=tier_sort_key)
    
    # Pass data to template
    return templates.TemplateResponse("aoe2civs.html", {
        "request": request,
        "title": "Age of Empires II Civilizations",
        "civilizations": sorted_civilizations
    })

app.mount("/static", StaticFiles(directory="app/static"), name="static")