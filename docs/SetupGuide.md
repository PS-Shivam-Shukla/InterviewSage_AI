# Setup Guide

## Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.10 |
| Node.js | 18 |
| npm | 9 |

No Docker, no cloud services, no external database required.

## Backend Setup

```bash
cd backend

# 1. Copy environment template
cp .env.example .env
```

Edit `.env`:
- `SECRET_KEY` — any long random string (e.g. `openssl rand -hex 32`)
- `LLM_API_KEY` — your OpenAI API key (or Anthropic key if using `LLM_PROVIDER=anthropic`)

```bash
# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Unix / macOS
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python -m alembic upgrade head

# 5. Start the server
python -m app.main
```

The API is now live at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

## Frontend Setup

```bash
cd frontend

# 1. Copy environment template
cp .env.example .env
# Default value (http://127.0.0.1:8000) works for local development

# 2. Install dependencies
npm install

# 3. Start the dev server
npm run dev
```

The UI is now live at `http://localhost:5173`.

## Running Tests

```bash
# Backend
cd backend
python -m pytest app/tests

# Frontend
cd frontend
npm test
```

## First-time Seed Data (optional)

To test without going through the UI, register via the API:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"mypassword","full_name":"Test User"}'
```

## Common Issues

**`alembic.ini` not found** — always run alembic commands from the `backend/` directory.

**`langchain_core` import error** — activate your virtualenv before running pytest: `venv\Scripts\activate`.

**CORS errors from frontend** — ensure the backend is running on `:8000` and frontend on `:5173`. Check `CORS_ORIGINS` in `.env`.

**LLM API key errors during tests** — tests use `FakeLLMClient` and never call the real API. If you see real API errors, confirm no test is bypassing the fake.
