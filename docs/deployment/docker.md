# Containerization & Docker Compose Guide

**InterviewSage AI Containerization Specification**

---

## 1. Container Images & Multi-Stage Builds

### 1.1 Backend Dockerfile (`backend/Dockerfile`)
- **Base Image**: `python:3.11-slim`
- **Build Strategy**: Multi-stage build (Builder stage compiles C-extensions, Runtime stage copies installed dependencies into clean environment).
- **Security**: Non-root system user (`appuser`, UID 10001) for strict CIS Docker benchmark compliance.
- **Healthcheck**: Automated `curl -f http://localhost:8000/health` probe every 30 seconds.

### 1.2 Frontend Dockerfile (`frontend/Dockerfile`)
- **Base Image**: `node:20-alpine` -> `nginx:alpine`
- **Build Strategy**: Multi-stage build (`npm run build` outputs Vite SPA bundle into Nginx web root).
- **Healthcheck**: Automated `wget --spider http://localhost/` probe every 20 seconds.

---

## 2. Service Orchestration (`docker-compose.yml`)

The production stack orchestrates 8 core containers:

1. **`postgres`**: PostgreSQL 16 database with persistent volume `interviewsage-postgres-data`.
2. **`redis`**: Redis 7 cache and distributed state store with appendonly persistence.
3. **`ollama`**: Local LLM inference engine serving Qwen2.5 / DeepSeek models.
4. **`backend`**: FastAPI application with LangGraph state machine & MCP tool server.
5. **`frontend`**: React 19 single-page application served via Nginx.
6. **`nginx`**: Front reverse proxy routing HTTP/WebSocket traffic with security headers & Gzip.
7. **`prometheus`**: Scrapes `/metrics` from backend service every 15s.
8. **`grafana`**: Observability dashboards on port 3000.

---

## 3. Operational Commands

```bash
# Start container stack in detached mode
docker compose up -d

# Rebuild containers after code updates
docker compose up -d --build

# Stop all container services
docker compose down

# Stop and wipe persistent volumes (CAUTION)
docker compose down -v
```
