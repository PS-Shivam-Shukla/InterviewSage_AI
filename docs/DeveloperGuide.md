# Developer Guide

## Folder Structure

```
L2_Interview_Sage_AI/
├── backend/
│   ├── alembic/               # Schema migrations
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   ├── app/
│   │   ├── main.py            # FastAPI app, router registration
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic BaseSettings (reads .env)
│   │   │   ├── database.py    # Engine, session factory, get_db()
│   │   │   ├── llm_client.py  # LLMClient + FakeLLMClient
│   │   │   ├── logging.py     # Structured JSON logging
│   │   │   └── security.py    # JWT, bcrypt
│   │   ├── api/v1/routes/     # HTTP route declarations (thin layer)
│   │   ├── agents/            # 12 specialist AI agents + base.py
│   │   ├── graph/
│   │   │   ├── state.py       # InterviewState TypedDict
│   │   │   └── graph_builder.py  # StateGraph assembly
│   │   ├── mcp/
│   │   │   ├── server.py      # MCPServer singleton
│   │   │   ├── tools/         # 7 tool implementations
│   │   │   └── resources/     # 3 resource handlers
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── prompts/           # Versioned prompt templates (v1.py per agent)
│   │   ├── repositories/      # Repository pattern (AbstractRepository)
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Business logic
│   │   └── tests/
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/               # Typed API functions (axios)
│   │   ├── components/
│   │   │   ├── charts/        # CompetencyRadar, ScoreTrendLine
│   │   │   ├── feedback/      # EmptyState, ErrorState
│   │   │   ├── interview/     # QuestionCard, EvaluationCard
│   │   │   ├── layout/        # Navbar, PageShell
│   │   │   └── ui/            # Button, Card, Badge, Dialog, FormField, ...
│   │   ├── context/           # AuthContext, ThemeContext
│   │   ├── hooks/             # useInterviewSession, useSSEStream
│   │   ├── pages/             # 13 pages (one folder each)
│   │   ├── styles/globals.css # Design tokens + Tailwind base
│   │   └── types/domain.ts    # TypeScript domain types
│   ├── package.json
│   └── vite.config.ts
│
└── docs/                      # This documentation set
```

## Coding Standards

- **Clean Architecture**: routes → services → repositories/agents. Inner layers never import outer.
- **Repository Pattern**: all SQL access through `*Repository` classes implementing `AbstractRepository[T]`.
- **Dependency Injection**: `FastAPI.Depends()` for DB sessions and current user. No global singletons at import time.
- **Strict TypeScript**: `strict: true` in `tsconfig.json`.
- **PEP 8**: enforced via `ruff` / `black`.
- **No inline f-string prompts**: all prompts in `app/prompts/{agent}/v{n}.py`.

## Adding a New Agent

1. Create `backend/app/agents/my_agent.py` inheriting `BaseAgent`:
   ```python
   class MyAgent(BaseAgent):
       agent_name = "MyAgent"
       prompt_version = "v1"

       def _run(self, state, retry_feedback=None):
           # ... call self.llm_client.invoke_structured(messages, MyOutput, retry_feedback)
           return {"my_output_key": result.model_dump()}

       def _on_failure(self, state, error):
           return {"my_output_key": {}, "error_log": [...]}
   ```
2. Create `backend/app/prompts/my_agent/v1.py` with `SYSTEM`, `DEVELOPER`, `VERSION = "v1"`.
3. Export from `backend/app/agents/__init__.py`.
4. Add a node in `graph_builder.py`:
   ```python
   graph.add_node("my_agent", my_agent_instance)
   graph.add_edge("previous_node", "my_agent")
   ```
5. Add a test in `app/tests/agents/test_agents.py` using `FakeLLMClient`.

## Adding a New MCP Tool

1. Implement in `backend/app/mcp/tools/my_tool.py`:
   ```python
   def my_tool(param1: str, param2: int) -> dict:
       ...
   ```
2. Register in `backend/app/mcp/__init__.py`:
   ```python
   mcp_server.register_tool(
       name="my_tool",
       description="...",
       parameters={"param1": {"type": "string"}, "param2": {"type": "integer"}},
       handler=my_tool,
       required_params=["param1"],
   )
   ```
3. Add a test in `app/tests/mcp/test_mcp_server.py`.

## Running Tests

```bash
# All backend tests with coverage
cd backend
python -m pytest app/tests -v

# Specific test file
python -m pytest app/tests/agents/test_agents.py -v

# All frontend tests
cd frontend
npm test
```

## Database Migrations

```bash
cd backend

# Apply all pending migrations
python -m alembic upgrade head

# Create a new migration (after changing ORM models)
python -m alembic revision --autogenerate -m "Add column foo"

# Rollback one migration
python -m alembic downgrade -1
```

## Environment Variables

See `backend/.env.example`. Required:
- `SECRET_KEY` — JWT signing key (any long random string)
- `LLM_API_KEY` — your LLM provider API key

Optional overrides:
- `LLM_PROVIDER` — `openai` (default) or `anthropic`
- `LLM_MODEL_NAME` — model to use (default `gpt-4`)
- `LLM_FALLBACK_MODEL` — fallback on primary failures (default `gpt-3.5-turbo`)
- `DATABASE_URL` — SQLite path (default `sqlite:///./interviewsage.db`)
