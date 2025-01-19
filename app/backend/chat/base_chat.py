import os
from dotenv import load_dotenv
import anthropic
from typing import List, Dict

class BaseChat:
    def __init__(self):
        # Load environment variables if ANTHROPIC_API_KEY is not set
        if not os.getenv("ANTHROPIC_API_KEY"):
            load_dotenv()
            
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    def format_messages(self, message: str, history: List[Dict] = None) -> List[Dict]:
        formatted_messages = []
        
        if history:
            for h in history:
                if isinstance(h, dict):
                    if h["role"] == "user":
                        formatted_messages.append({"role": "user", "content": h["content"]})
                    elif h["role"] == "assistant":
                        formatted_messages.append({"role": "assistant", "content": h["content"]})
        
        formatted_messages.append({"role": "user", "content": message})
        return formatted_messages

    async def get_response(self, message: str, history: List[Dict] = None) -> str:
        try:
            formatted_messages = self.format_messages(message, history)
            
            response = self.client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=1024,
                messages=formatted_messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return "I encountered an error processing your request. Please try again."