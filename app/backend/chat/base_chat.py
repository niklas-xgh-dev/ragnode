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
            
        # Create client without async context
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
    
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
        try:
            formatted_messages = self.format_messages(message, history)
            
            # Save user message
            await self.save_message("user", message)
            
            # Create a new client for each request
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=1024,
                messages=formatted_messages
            )
            
            response_text = response.content[0].text
            
            # Save assistant response
            await self.save_message("assistant", response_text)
            
            return response_text
            
        except anthropic.APIError as api_error:
            error_message = f"API Error: {str(api_error)}"
            print(error_message)
            await self.save_message("assistant", error_message)
            return error_message
            
        except anthropic.APIConnectionError as conn_error:
            error_message = "Connection to AI service failed. Please try again."
            print(f"Connection error: {str(conn_error)}")
            await self.save_message("assistant", error_message)
            return error_message
            
        except Exception as e:
            error_message = "I encountered an error processing your request. Please try again."
            print(f"Unexpected error in get_response: {str(e)}")
            await self.save_message("assistant", error_message)
            return error_message