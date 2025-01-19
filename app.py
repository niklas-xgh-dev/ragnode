# main.py
import os
from dotenv import load_dotenv
import gradio as gr
import anthropic
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Only load .env if ANTHROPIC_API_KEY is not in environment
if not os.getenv("ANTHROPIC_API_KEY"):
    load_dotenv()

# Initialize Anthropic client - will use environment variable or .env if available
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def chat_with_claude(message: str, history):
    try:
        formatted_messages = []
        
        if history:
            for h in history:
                if isinstance(h, dict):
                    if h["role"] == "user":
                        formatted_messages.append({"role": "user", "content": h["content"]})
                    elif h["role"] == "assistant":
                        formatted_messages.append({"role": "assistant", "content": h["content"]})
        
        formatted_messages.append({"role": "user", "content": message})
        
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1024,
            messages=formatted_messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        print(f"Error in chat_with_claude: {str(e)}")
        return "I encountered an error processing your request. Please try again."

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

js_func = open('app/static/gradio_force_theme.js', 'r').read()

# Create Gradio Chatbot and Gradio Chat Interface
with gr.Blocks(css="footer{display:none !important}", theme=gr.themes.Soft(), js=js_func) as chat_interface:
    with gr.Column(scale=1, min_width=600):
        chatbot = gr.Chatbot(
            height=700,
            type="messages",
            label="Chat"
        )
        gr.ChatInterface(
            fn=chat_with_claude,
            chatbot=chatbot,
            type="messages",
            examples=["What is a RAG? (in LLM context)", "Generate some Python code", "Is Batman good or evil?"],
        )

app = gr.mount_gradio_app(app, chat_interface, path="/chat/")
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)