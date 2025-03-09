import gradio as gr
import os
import yaml
import asyncio
from pathlib import Path
from .base_chat import BaseChat

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
        """
        Load the bot configuration from YAML file.
        
        Args:
            bot_id: ID of the bot
            
        Returns:
            Dict containing the bot configuration
        """
        if not bot_id:
            return {}
            
        # Path to config file
        config_file_path = f"app/config/{bot_id}-config.yaml"
        
        # Check if config file exists
        if not os.path.exists(config_file_path):
            print(f"No config file found for {bot_id}. Using empty config.")
            return {}
            
        try:
            # Load config from YAML
            with open(config_file_path, 'r') as file:
                config_data = yaml.safe_load(file)
                return config_data
                
        except Exception as e:
            print(f"Error loading config for {bot_id}: {str(e)}")
            return {}
    
    def _append_knowledge_base(self, bot_id: str, base_prompt: str) -> str:
        """
        Simple approach to append knowledge base content to the base prompt.
        
        Args:
            bot_id: ID of the bot
            base_prompt: The base system prompt for the bot
            
        Returns:
            Combined system prompt with knowledge base appended
        """
        if not bot_id:
            return base_prompt
            
        # Path to knowledge file
        knowledge_file_path = f"app/knowledge/{bot_id}.yaml"
        
        # Check if knowledge file exists
        if not os.path.exists(knowledge_file_path):
            print(f"No knowledge file found for {bot_id}. Using base prompt only.")
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
            print(f"Error loading knowledge for {bot_id}: {str(e)}")
            return base_prompt
    
    def get_examples(self):
        """
        Get examples from the bot configuration.
        
        Returns:
            List of example prompts
        """
        return self.config.get("examples", [])
        
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
                    # Add user message to history and return immediately
                    return "", history + [{"role": "user", "content": user_message}]
                    
                async def bot(history):
                    # Get the last user message
                    user_message = history[-1]["content"]
                    
                    # Add empty assistant message that will be updated during streaming
                    history.append({"role": "assistant", "content": ""})
                    
                    # Stream the response and update UI in real-time
                    async for full_response in self.chat.get_response(user_message, history[:-1]):
                        history[-1]["content"] = full_response
                        yield history
                
                # Add examples directly in the chat interface
                examples = self.get_examples()
                if examples:
                    with gr.Row():
                        example_buttons = []
                        for example in examples:
                            # Create a button for each example
                            example_btn = gr.Button(example, size="sm")
                            example_buttons.append(example_btn)
                            
                            # Set up event handler for the example button
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
    """
    Scan the config directory and return a dictionary of all available bots.
    
    Returns:
        Dict containing bot configurations
    """
    bots = {}
    config_dir = Path("app/config")
    
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