# Deployment Guide (Local Only)

InterviewSage AI v1 runs entirely on your local machine. There is no Docker, Kubernetes, cloud database, or external message broker — the only network call is the outbound HTTPS request to your LLM provider.

## Process model

Two processes run side-by-side:

| Process | Command | Default port |
|---|---|---|
| FastAPI backend | `python -m app.main` | 8000 |
| React dev server | `npm run dev` | 5173 |

The MCP server, LangGraph runtime, and SQLite database all run **inside** the Python process.

## Starting both servers

**Terminal 1 (backend):**
```bash
cd backend
venv\Scripts\activate     # Windows
source venv/bin/activate  # Unix/Mac
python -m app.main
```

**Terminal 2 (frontend):**
```bash
cd frontend
npm run dev
```

## Stopping cleanly

Press `Ctrl+C` in each terminal. The SQLite database persists between restarts — no data is lost.

## Ports and proxying

The Vite dev server proxies `/api/*` requests to the backend:

```js
// vite.config.ts
server: {
  proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } }
}
```

So the frontend only ever talks to `localhost:5173` and the proxy forwards API calls.

## Production build (optional)

To serve the built frontend from FastAPI (single-process mode):

```bash
cd frontend
npm run build
```

Then mount the `dist/` folder as a static directory in `backend/app/main.py`:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
```

## Database location

The SQLite file is at `backend/interviewsage.db`. Back it up by copying the file.

To reset all data:
```bash
cd backend
Remove-Item interviewsage.db    # Windows
rm interviewsage.db             # Unix/Mac
python -m alembic upgrade head  # re-create schema
```

## PostgreSQL migration path (future)

When ready to move to PostgreSQL:
1. Start a Postgres server and create a database.
2. Change `DATABASE_URL` in `.env` to `postgresql://user:pass@localhost:5432/interviewsage`.
3. Run `python -m alembic upgrade head` — the same migration files apply.
4. Run the one-time ETL script (to be provided in a future release) to copy SQLite data.
5. No agent or service code changes required — the Repository pattern abstracts all SQL access.
