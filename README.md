# Ragnode

A distributed RAG (Retrieval Augmented Generation) system deployed on AWS ECS, providing domain-specific knowledge embedding and retrieval through a streaming chat interface.

## Architecture Overview

Ragnode implements a cloud-native architecture combining FastAPI, Gradio, and Anthropic's Claude models via AWS Bedrock to create configurable bot interfaces with domain-specific knowledge.

### Core Components

- **LLM Integration**: AWS Bedrock API with Claude 3.7 Sonnet for high-quality text generation
- **Chat Engine**: Async streaming implementation with fallback mechanisms
- **Interface Layer**: Gradio-based chat interfaces dynamically mounted in FastAPI
- **Configuration**: YAML-based bot definitions with knowledge embeddings
- **Persistence**: Async SQLAlchemy ORM for conversation history
- **Deployment**: Containerized application running on AWS ECS Fargate

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS ECS Fargate                      │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────┐  │
│  │  FastAPI App   │◄───┤  Gradio Chat   │◄───┤ AWS Bedrock│  │
│  │                │    │  Interfaces    │    │ Claude API │  │
│  └───────┬────────┘    └────────────────┘    └────────────┘  │
│          │                                                    │
│          ▼                                                    │
│  ┌────────────────┐                                           │
│  │  PostgreSQL    │                                           │
│  │  (RDS)         │                                           │
│  └────────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Technical Implementation

### LLM Integration with AWS Bedrock

The system uses the AnthropicBedrock client to interact with Claude models:

```python
self.client = AnthropicBedrock(parameters)
```

Key features:
- Configurable model selection (defaults to `anthropic.claude-3-7-sonnet-20240229-v1:0`)
- Streaming response implementation with chunk processing
- Thread-safe asynchronous queue for response handling
- Non-streaming fallback mechanism

### Dynamic Bot Configuration

Bots are defined through YAML configuration files with standardized structure:

```yaml
id: bot-name
title: "Bot Display Name"
description: "Bot functionality description"
chat_path: "/bot-name/"
base_prompt: "System prompt for the bot"
examples:
  - "Example query 1"
  - "Example query 2"
```

Knowledge embedding is handled through associated YAML files containing domain-specific information that is appended to the system prompt.

### Async Message Streaming

The application implements a sophisticated message streaming system:

- Uses dedicated threads for API communication
- Implements async generator pattern for streaming responses
- Thread-safe message queue for cross-thread communication
- Timeout-based polling with graceful error handling
- Database persistence for conversation history

```python
async def get_response(self, message: str, history: List[Dict] = None) -> AsyncGenerator[str, None]:
    # Implementation handles streaming, threading, and persistence
    # ...
    chunk_queue = asyncio.Queue()
    # ...
    while True:
        try:
            chunk = await asyncio.wait_for(chunk_queue.get(), timeout=0.1)
            # Process chunks and yield responses
            yield full_response
        except asyncio.TimeoutError:
            # Handle timeouts
            continue
```

### FastAPI with Dynamic Gradio Integration

The system dynamically mounts Gradio interfaces for each configured bot:

```python
for bot_id, bot_config in bots.items():
    interface = ChatInterface(bot_id=bot_id).create_interface()
    gradio_apps.append(interface)
    chat_path = bot_config.get("chat_path", f"/{bot_id}/")
    app = gr.mount_gradio_app(app, interface, path=chat_path)
```

This approach allows:
- Multiple chat bots with different knowledge domains
- Dynamic routing based on configuration
- Unified template system with consistent UI

### Database Integration

The system uses SQLAlchemy with async session handling for conversation persistence:

```python
async def save_message(self, role: str, content: str) -> None:
    try:
        async with async_session() as session:
            msg = ChatMessage(role=role, content=content)
            session.add(msg)
            await session.commit()
    except Exception as e:
        print(f"Error saving {role} message to database: {str(e)}")
```

## Deployment Architecture

### Container Infrastructure

The application is containerized using Docker and deployed on AWS:

```
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### CI/CD Pipeline

Automated deployment pipeline using GitHub Actions:

1. Code push to main branch triggers workflow
2. Container build and push to ECR
3. ECS task definition update
4. Rolling deployment with health checks

## Development Guide

### Adding New Bots

1. Create a configuration file in `app/config/{bot-id}-config.yaml`
2. Define knowledge base in `app/knowledge/{bot-id}.yaml`
3. Optionally add deep knowledge in `app/deep_knowledge/{bot-id}/`
4. Restart the application to dynamically load the new bot

## Technical Roadmap

### Short-term Priorities

- Vector database integration for semantic search
- RAG pipeline optimization for knowledge retrieval
- Enhanced streaming performance
- Multi-model support with fallback options

## Dependencies

### Core Technologies

- **FastAPI**: Web framework with async support
- **Gradio**: UI components for chat interfaces
- **AWS Bedrock**: Managed LLM API access
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Relational database for persistence
- **Docker**: Containerization platform
- **AWS ECS**: Container orchestration

### AWS Services

- **Elastic Container Service (ECS)**: Container orchestration
- **Elastic Container Registry (ECR)**: Image repository
- **Relational Database Service (RDS)**: Managed PostgreSQL
- **Parameter Store**: Configuration management