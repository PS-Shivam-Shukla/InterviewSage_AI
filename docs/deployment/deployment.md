# Production Deployment Architecture Overview

**InterviewSage AI Platform**  
**Role**: Senior Principal DevOps Engineer & Infrastructure Architect

---

## 1. Environment Topology & Architecture

InterviewSage AI supports complete environment separation across Development, Staging, and Production deployment targets:

```
                            [ Client Web / Mobile / API ]
                                          │
                                          ▼
                            [ Nginx Front Reverse Proxy ]
                                   (Port 80 / 443)
                                          │
                ┌─────────────────────────┴─────────────────────────┐
                ▼                                                   ▼
      [ React 19 Frontend ]                              [ FastAPI Backend Service ]
       (Static SPA via Nginx)                                  (Port 8000)
                                                                    │
          ┌───────────────────────┬─────────────────────────┬───────┴───────────────┐
          ▼                       ▼                         ▼                       ▼
   [ PostgreSQL 16 ]       [ Redis 7 Cache ]         [ Ollama / LLM ]       [ Prometheus ]
   (Port 5432 DB)          (Port 6379 Cache)         (Port 11434 AI)        (Port 9090 Metrics)
```

---

## 2. Environment Profiles

| Environment | Database | Cache | Debug Mode | Logging | Log Format |
|---|---|---|:---:|:---:|:---:|
| **Development** | SQLite (`interviewsage.db`) / PG | Redis | `True` | `DEBUG` | Text |
| **Staging** | PostgreSQL (`interviewsage_staging`) | Redis | `False` | `INFO` | JSON |
| **Production** | PostgreSQL (`interviewsage_production`) | Redis | `False` | `INFO` | JSON |

---

## 3. Quickstart Deployment (Docker Compose)

```bash
# 1. Clone repository
git clone https://github.com/org/interview-sage-ai.git
cd interview-sage-ai

# 2. Configure environment file
cp .env.example .env.production

# 3. Launch full stack via Docker Compose
docker compose --env-file .env.production up -d --build

# 4. Verify deployment health
curl -f http://localhost/health
```

---

## 4. Subsystem Verification Commands

```bash
# View container status
docker compose ps

# Inspect backend logs
docker compose logs -f backend

# Run database migrations
docker compose exec backend alembic upgrade head

# Run automated backend test suite
docker compose exec backend pytest app/tests
```
