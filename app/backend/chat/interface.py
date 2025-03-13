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
            
        # Path to knowledge file
        knowledge_file_path = f"app/knowledge/{self.bot_id}.yaml"
        
        # Check if knowledge file exists
        if not os.path.exists(knowledge_file_path):
            return ""
            
        try:
            # Load knowledge from YAML
            with open(knowledge_file_path, 'r') as file:
                knowledge_data = yaml.safe_load(file)
                
            # Find relevant sections based on keywords
            relevant_data = {}
            
            print(f"Searching knowledge with keywords: {keywords}")
            
            # Convert yaml content to string for simple keyword searching
            knowledge_str = yaml.dump(knowledge_data, default_flow_style=False).lower()
            
            # First check if any keyword appears in the entire knowledge base
            if not any(keyword.lower() in knowledge_str for keyword in keywords if keyword):
                # If no keywords match at all, just return a small sample of the knowledge
                # This ensures we sometimes return knowledge even when keywords don't match
                sample_data = {}
                for key, value in list(knowledge_data.items())[:2]:  # Take first 2 sections
                    sample_data[key] = value
                
                print(f"No keyword matches, returning sample knowledge")
                return yaml.dump(sample_data, default_flow_style=False)
            
            # Extract sections containing keywords
            for key, value in knowledge_data.items():
                # Check if any keyword is in the key
                if any(keyword.lower() in key.lower() for keyword in keywords if keyword):
                    relevant_data[key] = value
                    continue
                
                # If value is a dictionary, check nested keys
                if isinstance(value, dict):
                    nested_match = {}
                    for nested_key, nested_value in value.items():
                        if any(keyword.lower() in nested_key.lower() for keyword in keywords if keyword):
                            nested_match[nested_key] = nested_value
                        # Check if keyword is in the nested value if it's a string
                        elif isinstance(nested_value, str) and any(keyword.lower() in nested_value.lower() for keyword in keywords if keyword):
                            nested_match[nested_key] = nested_value
                    
                    if nested_match:
                        relevant_data[key] = nested_match
                # Check if keyword is in the value if it's a string
                elif isinstance(value, str) and any(keyword.lower() in value.lower() for keyword in keywords if keyword):
                    relevant_data[key] = value
                # Check if it's a list and any item contains a keyword
                elif isinstance(value, list):
                    matching_items = []
                    for item in value:
                        if isinstance(item, str) and any(keyword.lower() in item.lower() for keyword in keywords if keyword):
                            matching_items.append(item)
                    if matching_items:
                        relevant_data[key] = matching_items
            
            if relevant_data:
                print(f"Found relevant knowledge sections: {list(relevant_data.keys())}")
                return yaml.dump(relevant_data, default_flow_style=False)
            
            # If no specific sections found but keywords exist in the content,
            # return a small sample of the knowledge
            sample_data = {}
            for key, value in list(knowledge_data.items())[:2]:  # Take first 2 sections
                sample_data[key] = value
            
            print(f"No specific sections found, returning sample knowledge")
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
                    # Get the last user message
                    user_message = history[-1]["content"]
                    
                    # Add empty assistant message that will be updated during streaming
                    history.append({"role": "assistant", "content": "🤔 Thinking..."})
                    yield history
                    
                    try:
                        # First, triage the request - this is a separate API call
                        history[-1]["content"] = "🤔 Analyzing your request..."
                        yield history
                        await asyncio.sleep(0.5)  # Short delay to make state visible
                        
                        option, reason = await self.chat.triage_request(user_message)
                        print(f"Triage decision: Option {option} - {reason}")
                        
                        # Process based on triage decision
                        if option == 1:  # Decline
                            history[-1]["content"] = f"I'm sorry, but I can't assist with that request. {reason}"
                            yield history
                            
                        elif option == 2:  # Retrieve knowledge
                            # Show retrieving state clearly
                            history[-1]["content"] = "🔍 I need to check my knowledge base for this..."
                            yield history
                            await asyncio.sleep(0.5)  # Short delay to make state visible
                            
                            # Extract keywords from the reason and query
                            all_text = f"{user_message} {reason}".lower()
                            # Extract words 4+ chars long as keywords
                            keywords = [word for word in all_text.split() if len(word) > 3]
                            print(f"Extracted keywords: {keywords}")
                            
                            # Get specific knowledge
                            additional_knowledge = self._get_specific_knowledge(keywords)
                            
                            if additional_knowledge:
                                history[-1]["content"] = "📚 Found relevant information! Let me answer now..."
                                yield history
                                await asyncio.sleep(0.5)  # Short delay to make state visible
                                
                                # Enhance the system prompt with the additional knowledge
                                enhanced_prompt = f"{self.base_prompt}\n\nHere is additional knowledge relevant to this question:\n{additional_knowledge}"
                                
                                # Temporarily set the system prompt to include knowledge
                                self.chat.system_prompt = enhanced_prompt
                                
                                # Get the response with the enhanced system prompt
                                async for full_response in self.chat.get_response(user_message, history[:-1]):
                                    history[-1]["content"] = full_response
                                    yield history
                                
                                # Reset the system prompt to base
                                self.chat.system_prompt = self.base_prompt
                            else:
                                history[-1]["content"] = "I couldn't find specific information about that. Let me answer based on what I know..."
                                yield history
                                await asyncio.sleep(0.5)  # Short delay to make state visible
                                
                                # Just use the base prompt if no specific knowledge found
                                async for full_response in self.chat.get_response(user_message, history[:-1]):
                                    history[-1]["content"] = full_response
                                    yield history
                            
                        else:  # Answer directly (option 3)
                            # Show answering state
                            history[-1]["content"] = "✍️ I know about this! Crafting response..."
                            yield history
                            await asyncio.sleep(0.5)  # Short delay to make state visible
                            
                            # Stream the response using base prompt
                            async for full_response in self.chat.get_response(user_message, history[:-1]):
                                history[-1]["content"] = full_response
                                yield history
                    
                    except Exception as e:
                        print(f"Error in bot function: {str(e)}")
                        history[-1]["content"] = f"I encountered an error while processing your request. Please try again."
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