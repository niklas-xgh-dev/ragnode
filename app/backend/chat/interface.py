import gradio as gr
import os
from .base_chat import BaseChat

class ChatInterface:
    def __init__(self):
        self.chat = BaseChat()
        
    def create_interface(self):
        js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              'static', 'gradio_force_theme.js')
        
        with open(js_path, 'r') as f:
            js_func = f.read()
        
        with gr.Blocks(css="footer{display:none !important}", theme=gr.themes.Soft(), js=js_func) as chat_interface:
            with gr.Column(scale=1, min_width=600):
                chatbot = gr.Chatbot(
                    height=700,
                    type="messages",
                    label="Chat"
                )
                gr.ChatInterface(
                    fn=self.chat.get_response,
                    chatbot=chatbot,
                    type="messages",
                    examples=[
                        "What is a RAG? (in LLM context)",
                        "Generate some Python code",
                        "Is Batman good or evil?"
                    ],
                )
        
        return chat_interface