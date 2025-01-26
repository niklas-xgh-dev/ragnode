import os
from dotenv import load_dotenv
import anthropic
from typing import List, Dict
from ..database import async_session
from ..models import ChatMessage

class BaseChat:
    def __init__(self, system_prompt: str = None):
        if not os.getenv("ANTHROPIC_API_KEY"):
            load_dotenv()
            
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.system_prompt = system_prompt
    
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

    async def save_message(self, role: str, content: str) -> None:
        try:
            async with async_session() as session:
                msg = ChatMessage(role=role, content=content)
                session.add(msg)
                await session.commit()
        except Exception as e:
            print(f"Error saving {role} message to database: {str(e)}")

    async def get_response(self, message: str, history: List[Dict] = None) -> str:
        if not message or message.strip() == "":
            return "Please enter a message."
            
        try:
            formatted_messages = self.format_messages(message, history)
            
            await self.save_message("user", message)
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=1024,
                system=self.system_prompt if self.system_prompt else None,
                messages=formatted_messages
            )
            
            response_text = response.content[0].text
            await self.save_message("assistant", response_text)
            return response_text
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(f"Error in get_response: {str(e)}")
            await self.save_message("assistant", error_message)
            return error_message