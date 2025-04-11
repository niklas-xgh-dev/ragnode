# Ragnode

A flexible platform for hosting chat bots with knowledge bases.

## Setup & Running

### Development Mode

Run both frontend and backend in development mode with:

```bash
./run-dev.sh
```

This will:
- Start the FastAPI backend at http://localhost:8000
- Start the Svelte frontend at http://localhost:3000
- Hot reload both on code changes

### Production Mode

For production deployment, run:

```bash
./run-prod.sh
```

This builds a single container serving both frontend and API on port 8000.

### Manual Build & Run

1. **Build frontend**:
   ```bash
   cd app/svelte
   npm install
   npm run build
   ```

2. **Run backend**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Adding New Bots

See [how2addbot.md](how2addbot.md) for detailed instructions.

## Architecture

- **Backend**: FastAPI + AWS Bedrock
- **Frontend**: Svelte + Tailwind CSS
- **Bots**: Configured via YAML files
- **Deployment**: Docker containers

## API Endpoints

- `/api/bots` - Get all available bots
- `/api/health` - Health check
- `/api/debug/bots` - Debug bot configurations

## URLs

- `/` - Home page with bot selection
- `/{bot_id}-chat` - Chat interface for specific bot