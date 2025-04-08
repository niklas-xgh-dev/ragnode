import os
from dotenv import load_dotenv
from anthropic import AnthropicBedrock
from typing import List, Dict, AsyncGenerator
import asyncio
import threading
import yaml
import gradio as gr
from pathlib import Path
from .database import async_session
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

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
        """Get a streaming response from Claude via AWS Bedrock."""
        if not message or message.strip() == "":
            yield "Please enter a message."
            return
            
        try:
            formatted_messages = self.format_messages(message, history)
            await self.save_message("user", message)
            
            client = self.get_client()
            chunk_queue = asyncio.Queue()
            streaming_done = [False]
            streaming_error = [None]
            
            def stream_in_thread():
                thread_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(thread_loop)
                
                try:
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
                    
                    for chunk in stream:
                        text = ""
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                            text = chunk.delta.text or ""
                        elif hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                            text = chunk.delta.content or ""
                        
                        if text:
                            thread_loop.run_until_complete(chunk_queue.put(text))
                            
                except Exception as e:
                    print(f"Error in streaming thread: {str(e)}")
                    streaming_error[0] = str(e)
                finally:
                    streaming_done[0] = True
                    thread_loop.run_until_complete(chunk_queue.put(None))
                    thread_loop.close()
            
            stream_thread = threading.Thread(target=stream_in_thread)
            stream_thread.daemon = True
            stream_thread.start()
            
            full_response = ""
            
            while True:
                if streaming_error[0]:
                    error_msg = f"Streaming error: {streaming_error[0]}"
                    await self.save_message("assistant", error_msg)
                    yield error_msg
                    return
                
                try:
                    chunk = await asyncio.wait_for(chunk_queue.get(), timeout=0.1)
                    if chunk is None:
                        break
                    
                    full_response += chunk
                    yield full_response
                    
                except asyncio.TimeoutError:
                    if streaming_done[0]:
                        break
                    continue
            
            if full_response:
                await self.save_message("assistant", full_response)
            
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


class ChatInterface:
    def __init__(self, bot_id: str = None):
        self.bot_id = bot_id
        self.config = self._load_config(bot_id)
        
        # Get the base prompt from the config
        base_prompt = self.config.get("base_prompt", "")
        
        # Append knowledge base if it exists
        system_prompt = self._append_knowledge_base(bot_id, base_prompt)
        
        self.chat = BaseChat(system_prompt=system_prompt)
    
    def _load_config(self, bot_id: str) -> dict:
        """Load the bot configuration from YAML file."""
        if not bot_id:
            return {}
            
        config_file_path = f"app/config/bots/{bot_id}-config.yaml"
        
        if not os.path.exists(config_file_path):
            print(f"No config file found for {bot_id}. Using empty config.")
            return {}
            
        try:
            with open(config_file_path, 'r') as file:
                config_data = yaml.safe_load(file)
                return config_data
                
        except Exception as e:
            print(f"Error loading config for {bot_id}: {str(e)}")
            return {}
    
    def _append_knowledge_base(self, bot_id: str, base_prompt: str) -> str:
        """Simple approach to append knowledge base content to the base prompt."""
        if not bot_id:
            return base_prompt
            
        knowledge_file_path = f"app/knowledge/{bot_id}.yaml"
        
        if not os.path.exists(knowledge_file_path):
            print(f"No knowledge file found for {bot_id}. Using base prompt only.")
            return base_prompt
            
        try:
            with open(knowledge_file_path, 'r') as file:
                knowledge_data = yaml.safe_load(file)
                
            knowledge_str = "\n\nHere is additional knowledge you have:\n"
            knowledge_str += yaml.dump(knowledge_data, default_flow_style=False)
            
            return base_prompt + knowledge_str
                
        except Exception as e:
            print(f"Error loading knowledge for {bot_id}: {str(e)}")
            return base_prompt
    
    def get_examples(self):
        """Get examples from the bot configuration."""
        return self.config.get("examples", [])
        
    def create_interface(self):
        js_path = os.path.join("app", "static", "gradio_force_theme.js")
        
        with open(js_path, 'r') as f:
            js_func = f.read()
        
        with gr.Blocks(css="footer{display:none !important}", theme=gr.themes.Default(), js=js_func) as chat_interface:
            with gr.Column(scale=1, min_width=600):
                chatbot = gr.Chatbot(
                    height=700,
                    type="messages",
                    label="Chat"
                )
                
                with gr.Row():
                    with gr.Column(scale=8):
                        msg = gr.Textbox(
                            show_label=False,
                            placeholder="Type your message here...",
                            container=True
                        )
                    with gr.Column(scale=1, min_width=50):
                        submit_btn = gr.Button("Send", variant="primary")
                
                async def user(user_message, history):
                    return "", history + [{"role": "user", "content": user_message}]
                    
                async def bot(history):
                    user_message = history[-1]["content"]
                    history.append({"role": "assistant", "content": ""})
                    
                    async for full_response in self.chat.get_response(user_message, history[:-1]):
                        history[-1]["content"] = full_response
                        yield history
                
                # Add examples directly in the chat interface
                examples = self.get_examples()
                if examples:
                    with gr.Row():
                        example_buttons = []
                        for example in examples:
                            example_btn = gr.Button(example, size="sm")
                            example_buttons.append(example_btn)
                            
                            example_btn.click(
                                fn=lambda example_text=example: example_text,
                                outputs=msg,
                                queue=False
                            ).then(
                                fn=user,
                                inputs=[msg, chatbot],
                                outputs=[msg, chatbot],
                                queue=False
                            ).then(
                                fn=bot,
                                inputs=[chatbot],
                                outputs=[chatbot]
                            )
                
                # Set up event handlers for regular user input
                msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
                    bot, chatbot, chatbot
                )
                submit_btn.click(user, [msg, chatbot], [msg, chatbot], queue=False).then(
                    bot, chatbot, chatbot
                )
                
                # Set a timeout for websocket connections
                if hasattr(chat_interface, '_queue'):
                    chat_interface._queue.timeout = 120  # 2-minute timeout for idle connections
        
        return chat_interface


# Helper function to get all available bot configs
def get_available_bots():
    """Scan the config directory and return a dictionary of all available bots."""
    bots = {}
    config_dir = Path("app/config/bots")
    
    if not config_dir.exists():
        return bots
        
    for config_file in config_dir.glob("*-config.yaml"):
        try:
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)
                
                if config and "id" in config:
                    bot_id = config["id"]
                    bots[bot_id] = config
                    
        except Exception as e:
            print(f"Error loading config from {config_file}: {str(e)}")
            
    return bots