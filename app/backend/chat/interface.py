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
        
        # Get the base prompt from the config without knowledge
        self.base_prompt = self.config.get("base_prompt", "")
        
        # Create chat instance with just the base prompt
        self.chat = BaseChat(system_prompt=self.base_prompt)
        
        # Track if knowledge was appended to avoid double appending
        self.knowledge_appended = False
    
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
    
    def _get_full_knowledge_base(self) -> str:
        """
        Get the full knowledge base content.
        
        Returns:
            String containing full knowledge base
        """
        if not self.bot_id:
            return ""
            
        # Path to knowledge file
        knowledge_file_path = f"app/knowledge/{self.bot_id}.yaml"
        
        # Check if knowledge file exists
        if not os.path.exists(knowledge_file_path):
            print(f"No knowledge file found for {self.bot_id}.")
            return ""
            
        try:
            # Load knowledge from YAML
            with open(knowledge_file_path, 'r') as file:
                knowledge_data = yaml.safe_load(file)
                
            # Convert knowledge to string representation
            return yaml.dump(knowledge_data, default_flow_style=False)
                
        except Exception as e:
            print(f"Error loading knowledge for {self.bot_id}: {str(e)}")
            return ""
    
    def _get_specific_knowledge(self, keywords: list) -> str:
        """
        Get specific sections of knowledge based on keywords.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            String with relevant knowledge sections
        """
        if not self.bot_id or not keywords:
            return ""
            
        knowledge_file_path = f"app/knowledge/{self.bot_id}.yaml"
        
        if not os.path.exists(knowledge_file_path):
            return ""
            
        try:
            # Load knowledge from YAML
            with open(knowledge_file_path, 'r') as file:
                knowledge_data = yaml.safe_load(file)
                
            # Convert to lowercase string for simple searching
            knowledge_str = yaml.dump(knowledge_data, default_flow_style=False).lower()
            
            # Check if any keyword appears in the knowledge
            has_matches = any(keyword.lower() in knowledge_str for keyword in keywords if keyword)
            
            if not has_matches:
                # Return a sample if no matches
                sample_data = dict(list(knowledge_data.items())[:2])
                return yaml.dump(sample_data, default_flow_style=False)
            
            # Extract relevant sections
            relevant_data = {}
            
            # First level search
            for key, value in knowledge_data.items():
                section_matched = False
                
                # Check key matches
                if any(keyword.lower() in key.lower() for keyword in keywords if keyword):
                    relevant_data[key] = value
                    continue
                
                # Check value content
                value_str = str(value).lower() if value else ""
                if any(keyword.lower() in value_str for keyword in keywords if keyword):
                    relevant_data[key] = value
                    continue
                
            # Return found data or a sample
            if relevant_data:
                return yaml.dump(relevant_data, default_flow_style=False)
            else:
                sample_data = dict(list(knowledge_data.items())[:2])
                return yaml.dump(sample_data, default_flow_style=False)
                
        except Exception as e:
            print(f"Error retrieving specific knowledge: {str(e)}")
            return ""
    
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
                    """
                    Bot response handler that ensures knowledge is never appended twice
                    when using Gradio's persistent history.
                    """
                    user_message = history[-1]["content"]
                    
                    # Initialize assistant message
                    history.append({"role": "assistant", "content": "Thinking..."})
                    yield history
                    
                    # IMPORTANT: Always reset to base prompt at the beginning of each turn
                    # This ensures any previously appended knowledge is removed
                    self.chat.system_prompt = self.base_prompt
                    
                    try:
                        # Triage the request
                        option, reason = await self.chat.triage_request(user_message)
                        
                        # Log the triage decision
                        print(f"\n{'='*50}")
                        print(f"TRIAGE DECISION: Option {option}")
                        print(f"  • 1=Decline, 2=Retrieve knowledge, 3=Answer directly")
                        print(f"  • Reason: {reason}")
                        print(f"  • User message: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'")
                        print(f"{'='*50}\n")
                        
                        if option == 1:  # Decline
                            history[-1]["content"] = f"I'm sorry, but I can't assist with that request. {reason}"
                            yield history
                            
                        elif option == 2:  # Retrieve knowledge
                            # Update status
                            history[-1]["content"] = "Checking knowledge base..."
                            yield history
                            
                            # Extract keywords
                            words = f"{user_message} {reason}".lower().split()
                            keywords = [word for word in words if len(word) > 3]
                            
                            # Get relevant knowledge
                            knowledge = self._get_specific_knowledge(keywords)
                            
                            if knowledge:
                                # Log that we're using knowledge for this response
                                print("Using knowledge for this response. Knowledge size:", len(knowledge))
                                
                                # Update status
                                history[-1]["content"] = "Checking knowledge base..."
                                yield history
                                
                                try:
                                    # Temporarily enhance the system prompt with knowledge JUST for this request
                                    enhanced_prompt = f"{self.base_prompt}\n\nRelevant knowledge:\n{knowledge}"
                                    self.chat.system_prompt = enhanced_prompt
                                    
                                    # Get response with knowledge
                                    async for response in self.chat.get_response(user_message, history[:-1]):
                                        history[-1]["content"] = response
                                        yield history
                                finally:
                                    # CRITICAL: Always reset to base prompt after response
                                    self.chat.system_prompt = self.base_prompt
                                    print("Reset system prompt to base version")
                            else:
                                print("No relevant knowledge found, using base knowledge")
                                # Fall back to base knowledge
                                async for response in self.chat.get_response(user_message, history[:-1]):
                                    history[-1]["content"] = response
                                    yield history
                        
                        else:  # Answer directly (option 3)
                            print("Using base knowledge (no retrieval)")
                            # Stream the response using base prompt
                            async for response in self.chat.get_response(user_message, history[:-1]):
                                history[-1]["content"] = response
                                yield history
                    
                    except Exception as e:
                        history[-1]["content"] = f"I encountered an error: {str(e)}"
                        yield history
                    
                    finally:
                        # Final safety check - make absolutely sure we reset to base prompt
                        # This ensures the next request starts fresh
                        self.chat.system_prompt = self.base_prompt
                        print("Final reset of system prompt to ensure clean state for next message")
                
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