# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
- Run backend: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Run frontend: `cd app/svelte && npm run dev`
- Build frontend: `cd app/svelte && npm run build`
- Docker build: `docker build -t ragnode .`
- Docker run: `docker run -p 8000:8000 --env-file .env ragnode`
- All-in-one: `./build.sh`

## Code Style Guidelines
- **Python**: Follow PEP 8 (snake_case for variables/functions, PascalCase for classes)
- **Imports**: Group imports (standard lib, third-party, local) with blank line separators
- **Error Handling**: Use specific exception types with logging
- **Async**: Use async/await patterns with proper error handling
- **Types**: Include type hints for function parameters and return values
- **Svelte**: Use Tailwind CSS for styling, component files should be single purpose
- **Naming**: Descriptive variable names that reveal intent
- **Config**: YAML-based configuration for bots in app/config/bots/
- **Knowledge**: YAML-based knowledge files in app/knowledge/

## Adding New Bots
See `how2addbot.md` for detailed instructions on adding new chatbots.