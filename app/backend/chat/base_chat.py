import os
from dotenv import load_dotenv
import anthropic
from typing import List, Dict, AsyncGenerator
import asyncio
from ..database import async_session
from ..models import ChatMessage

class BaseChat:
    def __init__(self, system_prompt: str = None):
        if not os.getenv("ANTHROPIC_API_KEY"):
            load_dotenv()
            
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.system_prompt = system_prompt
        self.client = None
    
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
    
    async def get_client(self):
        if self.client is None:
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self.client

    async def get_response(self, message: str, history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """
        Get a streaming response from Claude.
        
        Args:
            message: The user's message
            history: Chat history
            
        Yields:
            Chunks of the response text as they become available
        """
        if not message or message.strip() == "":
            yield "Please enter a message."
            return
            
        try:
            formatted_messages = self.format_messages(message, history)
            await self.save_message("user", message)
            
            client = await self.get_client()
            
            # Keep track of full response for saving to database
            full_response = ""
            
            # Stream the response
            async with client.messages.stream(
                model="claude-3-5-haiku-latest",
                max_tokens=1024,
                system=self.system_prompt if self.system_prompt else None,
                messages=formatted_messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield full_response  # Yield the cumulative response each time
            
            # Save the complete message to the database after streaming is complete
            await self.save_message("assistant", full_response)
                
        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(f"Error in get_response: {str(e)}")
            await self.save_message("assistant", error_message)
            yield error_message