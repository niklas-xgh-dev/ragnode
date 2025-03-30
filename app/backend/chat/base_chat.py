import os
from dotenv import load_dotenv
from anthropic import AnthropicBedrock
from typing import List, Dict, AsyncGenerator
import asyncio
import threading
from ..database import async_session
from ..models import ChatMessage

class BaseChat:
    def __init__(self, system_prompt: str = None):
        if not os.getenv("AWS_BEDROCK_ACCESS_KEY"):
            load_dotenv()
            
        # AWS Bedrock credentials
        self.aws_access_key = os.getenv("AWS_BEDROCK_ACCESS_KEY")
        self.aws_secret_key = os.getenv("AWS_BEDROCK_SECRET_KEY")
        self.aws_region = os.getenv("AWS_BEDROCK_REGION")
        self.region_prefix = os.getenv("AWS_BEDROCK_REGION_PREFIX", "")
        self.model_base = os.getenv("AWS_BEDROCK_MODEL_BASE", "anthropic.claude-3-7-sonnet-20240229-v1:0")
        
        # Generate full model ID
        if self.model_base.startswith(f"{self.region_prefix}."):
            self.model_id = self.model_base
        else:
            self.model_id = f"{self.region_prefix}.{self.model_base}"
        
        print(f"Using model ID: {self.model_id}")
        
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
    
    def get_client(self):
        if self.client is None:
            # Use AnthropicBedrock client
            self.client = AnthropicBedrock(
                aws_access_key=self.aws_access_key,
                aws_secret_key=self.aws_secret_key,
                aws_region=self.aws_region
            )
        return self.client

    async def get_response(self, message: str, history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """
        Get a streaming response from Claude via AWS Bedrock.
        
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
            
            client = self.get_client()
            
            # Create a thread-safe queue for passing chunks between threads
            chunk_queue = asyncio.Queue()
            
            # Flag to signal when streaming is complete
            # Using a list so it can be modified inside the inner function
            streaming_done = [False]
            streaming_error = [None]
            
            # Function to run in a separate thread
            def stream_in_thread():
                # Create a new event loop for this thread
                thread_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(thread_loop)
                
                try:
                    # Initialize stream
                    stream = client.messages.create(
                        model=self.model_id,
                        max_tokens=2048,
                        temperature=0.7,
                        top_p=0.999,
                        top_k=250,
                        system=self.system_prompt if self.system_prompt else None,
                        messages=formatted_messages,
                        stream=True
                    )
                    
                    # Process each chunk
                    for chunk in stream:
                        text = ""
                        
                        # Extract text from chunk
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                            text = chunk.delta.text or ""
                        elif hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                            text = chunk.delta.content or ""
                        
                        if text:
                            # Put the chunk in the queue using the thread's event loop
                            thread_loop.run_until_complete(chunk_queue.put(text))
                            
                except Exception as e:
                    # If there's an error, put it in the error holder
                    print(f"Error in streaming thread: {str(e)}")
                    streaming_error[0] = str(e)
                finally:
                    # Signal that streaming is done
                    streaming_done[0] = True
                    # Send a signal to the queue
                    thread_loop.run_until_complete(chunk_queue.put(None))
                    thread_loop.close()
            
            # Start the streaming thread
            stream_thread = threading.Thread(target=stream_in_thread)
            stream_thread.daemon = True
            stream_thread.start()
            
            # Process chunks from the queue in the main async function
            full_response = ""
            
            while True:
                # Check for errors first
                if streaming_error[0]:
                    error_msg = f"Streaming error: {streaming_error[0]}"
                    await self.save_message("assistant", error_msg)
                    yield error_msg
                    return
                
                try:
                    # Get chunk with a timeout
                    chunk = await asyncio.wait_for(chunk_queue.get(), timeout=0.1)
                    
                    # None signals the end of streaming
                    if chunk is None:
                        break
                    
                    # Add the chunk to the full response
                    full_response += chunk
                    
                    # Yield the updated full response
                    yield full_response
                    
                except asyncio.TimeoutError:
                    # Check if streaming is done
                    if streaming_done[0]:
                        break
                    # Otherwise, continue waiting
                    continue
            
            # Save the complete response to the database
            if full_response:
                await self.save_message("assistant", full_response)
            
            # If streaming returned an empty response, try the non-streaming fallback
            if not full_response and not streaming_error[0]:
                print("Streaming returned an empty response. Trying non-streaming fallback.")
                
                def get_non_streaming_response():
                    try:
                        response = client.messages.create(
                            model=self.model_id,
                            max_tokens=2048,
                            temperature=0.7,
                            top_p=0.999,
                            top_k=250,
                            system=self.system_prompt if self.system_prompt else None,
                            messages=formatted_messages
                        )
                        content = ""
                        if hasattr(response, 'content'):
                            if isinstance(response.content, list):
                                for block in response.content:
                                    if hasattr(block, 'text'):
                                        content += block.text
                                    elif isinstance(block, dict) and 'text' in block:
                                        content += block['text']
                            else:
                                content = response.content
                        return {"success": True, "response": content}
                    except Exception as e:
                        print(f"Non-streaming error: {str(e)}")
                        return {"success": False, "error": str(e)}
                
                loop = asyncio.get_event_loop()
                fallback_result = await loop.run_in_executor(None, get_non_streaming_response)
                
                if fallback_result["success"]:
                    fallback_response = fallback_result["response"]
                    await self.save_message("assistant", fallback_response)
                    yield fallback_response
                else:
                    error_message = f"Error: {fallback_result.get('error', 'Both streaming and non-streaming failed')}"
                    await self.save_message("assistant", error_message)
                    yield error_message
                
        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(f"Error in get_response: {str(e)}")
            await self.save_message("assistant", error_message)
            yield error_message