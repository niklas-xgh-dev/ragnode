import os
from dotenv import load_dotenv
import anthropic
from typing import List, Dict
from ..database import async_session
from ..models import ChatMessage

class BaseChat:
    def __init__(self):
        if not os.getenv("ANTHROPIC_API_KEY"):
            load_dotenv()
            
        self.client = anthropic.AsyncAnthropic(
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
            
            # Save user message
            async with async_session() as session:
                user_msg = ChatMessage(role="user", content=message)
                session.add(user_msg)
                await session.commit()
            
            # Get AI response
            async with self.client as client:
                response = await client.messages.create(
                    model="claude-3-5-haiku-latest",
                    max_tokens=1024,
                    messages=formatted_messages
                )
            
            response_text = response.content[0].text
            
            # Save assistant response
            async with async_session() as session:
                assistant_msg = ChatMessage(role="assistant", content=response_text)
                session.add(assistant_msg)
                await session.commit()
            
            return response_text
            
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return "I encountered an error processing your request. Please try again."