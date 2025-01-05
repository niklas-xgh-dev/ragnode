# Ragnode

A distributed RAG (Retrieval Augmented Generation) system deployed on AWS ECS, designed for domain-specific knowledge embedding and retrieval.

## System Architecture

### Core Components

- **RAG Engine**: Python-based retrieval system utilizing vector embeddings for semantic search
- **API Layer**: FastAPI implementation with async handlers
- **Frontend**: Minimalist architecture using vanilla HTML/HTMX with Gradio chatbot integration
- **Persistence**: PostgreSQL for vector storage and metadata management
- **Infrastructure**: AWS ECS deployment with automated GitHub Actions pipeline

### Repository Structure

The system is split into two repositories:

```
ragnode/                      # Main application code
├── app/
│   ├── backend/
│   │   ├── main.py          # FastAPI application entrypoint
│   │   ├── embeddings/      # Embedding generation and management
│   │   ├── retrieval/       # RAG implementation
│   │   └── api/             # REST endpoints
│   └── frontend/            # HTMX/vanilla JS implementation
│
└── .github/                 # CI workflows

ragnode-infra/               # Private infrastructure repository
├── scripts/                 # Infrastructure management scripts
├── .github/                 # Infrastructure deployment workflows
└── config/                  # ECS task definitions and configurations
```

## Technical Implementation

### RAG Implementation

- Vector embedding generation using transformer-based models
- Semantic search optimization with approximate nearest neighbors
- Configurable context window management
- Streaming response handling via SSE

### AWS Infrastructure

The application runs on AWS with the following components:

- **ECS (Elastic Container Service)**
  - Application runs in Fargate tasks
  - Auto-scaling based on CPU/memory metrics
  - Task definitions managed via GitHub Actions
  
- **ECR (Elastic Container Registry)**
  - Stores Docker images
  - Automated image pushing on main branch updates
  
- **RDS**
  - PostgreSQL instance for data persistence
  - Vector similarity search capabilities
  
- **Parameter Store**
  - Stores configuration and environment variables
  - Tracks container IP for service discovery

## Continuous Deployment

Automated deployment pipeline using GitHub Actions:

1. Code push to main branch triggers workflow in infrastructure repository
2. Workflow builds and pushes new Docker image to ECR
3. Updates ECS service to use new image
4. Updates container IP in Parameter Store for service discovery

```yaml
name: Deploy to AWS
on:
  repository_dispatch:
    types: [code-push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Build and push to ECR
      - name: Deploy to ECS
      - name: Update container IP
#etc...
```

## Current Development Focus

- Vector database optimization for large-scale embeddings
- Enhanced semantic search algorithms
- Integration of additional embedding models
- Real-time data ingestion pipeline
- Advanced caching strategies

## Future Technical Roadmap

### Near-term
- ECS service auto-scaling based on queue depth
- Enhanced prompt engineering for context injection
- Streaming response optimization
- Advanced monitoring and alerting setup

### Long-term
- Multi-model embedding support
- Advanced vector compression techniques
- Real-time embedding updates
- Custom embedding model training
- Enhanced vector similarity search algorithms
- Integration with additional LLM providers

## Technical Dependencies

Core Dependencies:
- FastAPI
- Anthropic Claude API
- PostgreSQL
- HTMX
- Gradio
- Docker

AWS Services:
- ECS (Fargate)
- ECR
- RDS
- Parameter Store
- CloudWatch
- IAM

## Development Notes

The system is designed for high scalability and maintainability:
- Stateless application design
- Containerized services
- GitHub Actions for automated deployment
- Centralized configuration management
- Automated testing and deployment