# InterviewSage AI - Backend

## Overview

Backend for InterviewSage AI - An Agentic AI Interview Simulation Platform powered by Multi-Agent Systems, LangGraph, Model Context Protocol (MCP), and Large Language Models.

## Architecture

- **Framework**: FastAPI
- **Orchestration**: LangGraph (multi-agent state machine)
- **Database**: SQLite (PostgreSQL-ready)
- **AI/LLM**: LangChain abstraction layer
- **Tool Protocol**: Model Context Protocol (MCP)
- **Voice Streaming**: Dual-Engine Architecture (FasterWhisper STT + Kokoro TTS with local synthetic fallback handlers)
- **Testing**: Pytest

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/                   # Core configuration and utilities
│   │   ├── config.py          # Settings (Pydantic BaseSettings)
│   │   └── logging.py         # Structured logging setup
│   ├── api/v1/routes/         # API route definitions
│   ├── controllers/           # Request/response orchestration
│   ├── services/              # Business logic layer
│   ├── agents/                # 13 specialized AI agents
│   ├── graph/                 # LangGraph state machine
│   ├── mcp/                   # Model Context Protocol server
│   │   ├── tools/            # MCP tool implementations
│   │   ├── resources/        # MCP resource providers
│   │   └── prompts/          # MCP prompt registry
│   ├── prompts/               # Versioned agent prompt templates
│   ├── schemas/               # Pydantic models
│   ├── models/                # SQLAlchemy ORM models
│   ├── repositories/          # Data access layer (Repository pattern)
│   ├── dependencies/          # FastAPI dependencies
│   ├── middlewares/           # Auth, CORS, logging middleware
│   ├── utils/                 # Shared utilities
│   └── tests/                 # Test suite
├── alembic/                   # Database migrations
├── uploads/                   # Resume/JD file storage
├── logs/                      # Application logs
├── requirements.txt           # Python dependencies
└── .env.example              # Environment variables template
```

## Setup

### Prerequisites

- Python 3.10+
- pip or uv

### Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from template:
```bash
cp .env.example .env
```

4. Edit `.env` and set required values:
   - `SECRET_KEY`: Generate a secure random key
   - `LLM_API_KEY`: Your LLM provider API key

### Running the Application

Development mode with auto-reload:
```bash
python -m app.main
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### API Documentation

Once running, access:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health Check: http://127.0.0.1:8000/health

## Testing

Run the full test suite:
```bash
pytest
```

With coverage report:
```bash
pytest --cov=app --cov-report=html
```

## Continuous Integration

This repository includes a GitHub Actions workflow that runs the backend test suite on push and pull requests.

- Workflow: `.github/workflows/python-tests.yml`

CI runs the following commands (from the repo root):

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
```

## Contributing / PR checklist

- Run tests locally before opening a PR:

```bash
cd backend
pytest -q
```

- Follow the PR template: `.github/PULL_REQUEST_TEMPLATE.md`


## Development

### Code Quality

Format code with black:
```bash
black app/
```

Lint with ruff:
```bash
ruff check app/
```

Type check with mypy:
```bash
mypy app/
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

## Architecture Highlights

### Multi-Agent System

InterviewSage AI uses 13 specialized AI agents orchestrated by LangGraph:

1. **Supervisor Agent** - Central router
2. **Resume Agent** - Resume parsing and analysis
3. **JD Analysis Agent** - Job description extraction
4. **ATS Agent** - Resume-JD alignment scoring
5. **Profile Intelligence Agent** - Candidate profile synthesis
6. **Competency Mapping Agent** - Weighted competency matrix generation
7. **Interview Planner Agent** - Interview structure planning
8. **Question Generator Agent** - Context-rich question generation
9. **HR Interview Agent** - Behavioral interview conductor
10. **Technical Interview Agent** - Technical interview conductor
11. **Evaluation Agent** - Answer scoring and feedback
12. **Career Coach Agent** - Improvement plan generation
13. **Report Generator Agent** - Final report compilation

### Clean Architecture

- **Routes** → HTTP contract only
- **Controllers** → Request/response translation
- **Services** → Business logic
- **Repositories** → Data access (Repository pattern)
- **Agents** → AI reasoning units
- **Graph** → Orchestration (LangGraph)

### Model Context Protocol (MCP)

All agent capabilities (tools, resources, prompts) are exposed through a unified MCP server, enabling:
- Discoverable, permissioned tool access
- Centralized capability governance
- Clean separation of reasoning (agents) from implementation (tools)

## License

Proprietary - InterviewSage AI
