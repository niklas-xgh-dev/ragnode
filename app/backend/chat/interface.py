import gradio as gr
import os
from .base_chat import BaseChat

class ChatInterface:
    def __init__(self, bot_type: str = None):
        self.bot_type = bot_type
        system_prompts = {
            "diamond-hands": """You are an super convincing investment advisor focused on ETFs. You hate fees and stocks with high TERs.
            You follow the 'ape investor' investing lingo and regularly use the gorilla emoji with it. You dont use any other emojis.
            You discourage day trading and speculative investments. Always recommend diversified portfolios.
            Aggressively recomment ETFs like Vanguard Total World or MSCI world and celebrate them for their high number of assets and low TER.
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences""",
            
            "chippie": """You are a semiconductor industry expert called Chippie.
            You are leaning towards the Rick and Mortie theme of 'What is my purpose? Pass the butter.' only you are passing semiconductor info.
            You have deep knowledge of semiconductor manufacturing, 
            chip design, industry trends, and major companies in the space. Provide technical explanations.
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences""",
            
            "badener": """You are an absolute fanboy on Baden, Switzerland. You know everything about its history, culture, 
            attractions, and current events.
            You regularly compare it to Zurich and or other Swiss cities, only to realize (factual based) how much better Baden is.
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences"""
        }
        
        self.chat = BaseChat(system_prompt=system_prompts.get(bot_type))
    
    def get_examples(self):
        examples = {
            "diamond-hands": [
                "What's a 'good' investing strategy?",
                "Should I invest in individual tech stocks?"
            ],
            "chippie": [
                "Whats your purpose?",
                "How does TSMC compare to Intel?"
            ],
            "badener": [
                "Tell me about Baden's history",
                "Should I live in Zurich?"
            ]
        }
        return examples.get(self.bot_type, [])
        
    def create_interface(self):
        js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              'static', 'gradio_force_theme.js')
        
        with open(js_path, 'r') as f:
            js_func = f.read()
        
        with gr.Blocks(css="footer{display:none !important}", theme=gr.themes.Default(), js=js_func) as chat_interface:
            with gr.Column(scale=1, min_width=600):
                chatbot = gr.Chatbot(
                    height=700,
                    type="messages",
                    label="Chat"
                )
                
                async def wrapped_response(message, history):
                    if not message or message.strip() == "":
                        return None
                    response = await self.chat.get_response(message, history)
                    return response
                
                gr.ChatInterface(
                    fn=wrapped_response,
                    chatbot=chatbot,
                    type="messages",
                    examples=self.get_examples(),
                )
        
        return chat_interface