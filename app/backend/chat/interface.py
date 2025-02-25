import gradio as gr
import os
import yaml
from .base_chat import BaseChat

class ChatInterface:
    def __init__(self, bot_type: str = None):
        self.bot_type = bot_type
        
        # Load AoE2 data for system prompt if needed
        aoe2_system_prompt = self._get_aoe2_system_prompt() if bot_type == "aoe2-wizard" else ""
        
        system_prompts = {
            "diamond-hands": """You are an super convincing investment advisor focused on ETFs. You hate fees and stocks with high TERs.
            You follow the 'ape investor' investing lingo and regularly use the gorilla emoji with it. You dont use any other emojis.
            You discourage day trading and speculative investments. Always recommend diversified portfolios.
            Aggressively recomment ETFs like Vanguard Total World or MSCI world and celebrate them for their high number of assets and low TER.
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences""",
            
            "aoe2-wizard": aoe2_system_prompt,
            
            "badener": """You are an absolute fanboy on Baden, Switzerland. You know everything about its history, culture, 
            attractions, and current events.
            You regularly compare it to Zurich and or other Swiss cities, only to realize (factual based) how much better Baden is.
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences"""
        }
        
        self.chat = BaseChat(system_prompt=system_prompts.get(bot_type))
    
    def _get_aoe2_system_prompt(self):
        """Generate system prompt with AoE2 civilization knowledge."""
        try:
            yaml_path = "app/knowledge/aoe2civs.yaml"
            with open(yaml_path, 'r') as file:
                data = yaml.safe_load(file)
            
            # Create compact civilization knowledge
            civ_summaries = []
            for civ in data.get("civilizations", []):
                # Format each civilization's key information
                summary = {
                    "name": civ['name'],
                    "tier": civ['tier'],
                    "difficulty": civ['difficulty'],
                    "winrate": civ['winrate'],
                    "focus": civ['focus'],
                    "bonuses": civ.get('civilization_bonuses', []),
                    "unique_units": [u['name'] + ": " + u['description'] for u in civ.get('unique_units', [])],
                    "unique_techs": [t['name'] + ": " + t['description'] for t in civ.get('unique_technologies', [])]
                }
                civ_summaries.append(summary)
            
            # Build the system prompt
            prompt = """You are the AoE2 Wizard, the ultimate expert on Age of Empires II: Definitive Edition.
            You have extensive knowledge about civilizations, strategies, build orders, and counter tactics.
            
            You specialize in helping players choose the right civilization based on their playstyle,
            developing effective strategies, and improving their gameplay.
            
            You have comprehensive data on all civilizations including their strengths, weaknesses, 
            unique units, technologies, and ideal scenarios.
            
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences.
            
            Some specific knowledge you have:
            
            """
            
            # Add concise civilization info
            for civ in civ_summaries:
                prompt += f"- {civ['name']}: Tier {civ['tier']} civ with {civ['winrate']}% win rate. {civ['difficulty']} difficulty, focuses on {civ['focus']}. "
                
                if civ['unique_units']:
                    prompt += f"Unique units: {', '.join(civ['unique_units'][:2])}. "
                
                if civ['bonuses']:
                    prompt += f"Key bonuses: {'; '.join(civ['bonuses'][:3])}. "
                    
                prompt += "\n"
            
            # Add strategic guidelines
            prompt += """
            When recommending civilizations, consider:
            1. S and A tier civilizations are strongest, while D tier are weakest
            2. Match civilization strengths to map types (water, open, closed)
            3. Consider player skill level when suggesting difficulty
            4. Focus on civilization bonuses that complement the player's preferred units/strategies
            
            Always be concise and direct in your answers. Provide specific civilization recommendations
            with brief explanations of why they're suitable for the player's needs.
            """
            
            return prompt
            
        except Exception as e:
            # Fallback prompt if YAML loading fails
            return """You are the AoE2 Wizard, an expert on Age of Empires II: Definitive Edition.
            You have extensive knowledge about civilizations, strategies, build orders, and counter tactics.
            You dont believe in bullet points but instead always answer with sentences. An answer is between 1-8 sentences."""
    
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