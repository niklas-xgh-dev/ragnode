import os
from dotenv import load_dotenv
import anthropic
from typing import List, Dict, AsyncGenerator, Tuple
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

    async def triage_request(self, message: str) -> Tuple[int, str]:
        """
        Triage the user request to determine the appropriate action.
        
        Args:
            message: The user's message
            
        Returns:
            Tuple containing (option, reason)
            option: 1 = Decline, 2 = Retrieve knowledge, 3 = Answer directly
        """
        try:
            client = await self.get_client()
            
            # Extract a brief context about the assistant's role
            role_context = ""
            if self.system_prompt:
                prompt_lines = self.system_prompt.split('\n')
                role_context = '\n'.join(prompt_lines[:min(5, len(prompt_lines))])
            
            triage_prompt = f"""
            You are a triage assistant that determines how to handle user requests.
            
            Here is information about the assistant's role:
            {role_context}
            
            For each user request, categorize it into ONE of these options:
            
            1. DECLINE: The request is not relevant to your knowledge domain.
            2. RETRIEVE: The request requires specific facts or information from a knowledge base.
            3. ANSWER: The request can be answered with general knowledge.
            
            RESPOND EXACTLY IN THIS FORMAT:
            OPTION: [1 or 2 or 3]
            REASON: [brief explanation]
            """
            
            response = await client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=150,
                system=triage_prompt,
                messages=[{"role": "user", "content": f"Request: {message}"}],
            )
            
            decision_text = response.content[0].text.strip()
            
            # More streamlined parsing
            option = 3  # Default to answer directly
            reason = "Using foundational knowledge"
            
            if "OPTION: 1" in decision_text or "OPTION:1" in decision_text:
                option = 1
            elif "OPTION: 2" in decision_text or "OPTION:2" in decision_text:
                option = 2
            
            # Extract reason regardless of option
            if "REASON:" in decision_text:
                reason = decision_text.split("REASON:", 1)[1].strip()
            
            return option, reason
                
        except Exception as e:
            print(f"Error in triage_request: {str(e)}")
            return 3, f"Error during triage: {str(e)}"

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