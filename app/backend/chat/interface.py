import gradio as gr
import os
import yaml
from .base_chat import BaseChat

class ChatInterface:
    def __init__(self, bot_type: str = None):
        self.bot_type = bot_type
        
        # Define base prompts for each bot type
        base_prompts = {
            "diamond-hands": """You are an super convincing investment advisor focused on ETFs. You hate fees and stocks with high TERs.
            You follow the 'ape investor' investing lingo and regularly use the gorilla emoji with it. You dont use any other emojis.
            You discourage day trading and speculative investments. Always recommend diversified portfolios.
            Aggressively recomment ETFs like Vanguard Total World or MSCI world and celebrate them for their high number of assets and low TER.
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences""",
            
            "aoe2-wizard": """You are the AoE2 Wizard, the ultimate expert on Age of Empires II: Definitive Edition.
            You have extensive knowledge about civilizations, strategies, build orders, and counter tactics.
            
            You specialize in helping players choose the right civilization based on their playstyle,
            developing effective strategies, and improving their gameplay.
            
            You have comprehensive data on all civilizations including their strengths, weaknesses, 
            unique units, technologies, and ideal scenarios.
            
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences.""",
            
            "badener": """You are an absolute fanboy on Baden, Switzerland. You know everything about its history, culture, 
            attractions, and current events.
            You regularly compare it to Zurich and or other Swiss cities, only to realize (factual based) how much better Baden is.
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences"""
        }
        
        # Get the base prompt for this bot type
        base_prompt = base_prompts.get(bot_type, "")
        
        # Append knowledge base if it exists
        system_prompt = self._append_knowledge_base(bot_type, base_prompt)
        
        self.chat = BaseChat(system_prompt=system_prompt)
    
    def _append_knowledge_base(self, bot_type: str, base_prompt: str) -> str:
        """
        Simple approach to append knowledge base content to the base prompt.
        
        Args:
            bot_type: Type of the bot
            base_prompt: The base system prompt for the bot
            
        Returns:
            Combined system prompt with knowledge base appended
        """
        if not bot_type:
            return base_prompt
            
        # Path to knowledge file
        knowledge_file_path = f"app/knowledge/{bot_type}.yaml"
        
        # Check if knowledge file exists
        if not os.path.exists(knowledge_file_path):
            print(f"No knowledge file found for {bot_type}. Using base prompt only.")
            return base_prompt
            
        try:
            # Load knowledge from YAML
            with open(knowledge_file_path, 'r') as file:
                knowledge_data = yaml.safe_load(file)
                
            # Convert knowledge to string representation and append to base prompt
            knowledge_str = "\n\nHere is additional knowledge you have:\n"
            knowledge_str += yaml.dump(knowledge_data, default_flow_style=False)
            
            return base_prompt + knowledge_str
                
        except Exception as e:
            print(f"Error loading knowledge for {bot_type}: {str(e)}")
            return base_prompt
    
    def get_examples(self):
        examples = {
            "diamond-hands": [
                "What's a 'good' investing strategy?",
                "Should I invest in individual tech stocks?"
            ],
            "aoe2-wizard": [
                "What are the best civilizations for water maps?",
                "Recommend a civilization for a beginner",
                "How do I best counter knight rushes?",
                "What's a good build order for Franks?"
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