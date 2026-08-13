# InterviewSage AI

An AI interview simulation and telemetry platform built with FastAPI, LangGraph, React 19, TypeScript, and OpenTelemetry.

---

## Overview

**InterviewSage AI** is a full-stack platform designed to automate and analyze technical and behavioral interview workflows. The system ingests candidate resumes and job descriptions, classifies candidate seniority, builds structured interview plans via a **Dynamic Interview Strategy Engine (DISE)**, executes multi-turn question-and-answer sessions via a **LangGraph StateGraph** workflow, scores answers using an **AI Kernel**, and generates competency reports with PDF downloads.

The repository includes a FastAPI backend, a React 19 frontend SPA, an in-process **Model Context Protocol (MCP)** server, local Speech-to-Text (STT) and Text-to-Speech (TTS) voice modules, and containerized deployment configuration via Docker Compose.

---

## Problem Statement

Technical and behavioral interview preparation and evaluation often suffer from inconsistent scoring criteria, manual effort in aligning candidate resumes against job description requirements, and lack of real-time telemetry during practice interviews. Candidates lack personalized feedback tied to specific job description skill gaps, while organizations require structured candidate evaluation blueprints with reproducible assessment metrics.

---

## Solution

InterviewSage AI addresses these challenges by combining:

1. **Resume & Job Description Analysis**: Extracting structured skill graphs and parsing requirements from uploaded PDF/Docx files.
2. **Dynamic Interview Strategy Engine (DISE)**: Classifying candidate seniority levels (Junior, Mid, Senior, Lead, Principal) and generating tailored evaluation blueprints.
3. **LangGraph State Graph Workflow**: Managing interview state, question personalization, and turn-by-turn answer evaluation.
4. **AI Kernel Resiliency**: Enforcing system prompt templates, PII masking, prompt injection guardrails, and model routing.
5. **Real-Time Telemetry & Observability**: Exposing execution metrics (Prometheus), OpenTelemetry tracing hooks, and cluster node metrics.
6. **In-Process MCP Server**: Exposing internal tools and resources for structured agent invocations.

---

## Key Features

- 🔐 **Authentication & Session Security**: JWT-based authentication (HS256) with BCrypt password hashing, session context tracking, and security HTTP headers (`nosniff`, `DENY`, `strict-origin-when-cross-origin`).
- 📊 **Command Dashboard**: Overview dashboard displaying interview stats, active session status, recent score distribution, and quick action launchpads.
- 🎯 **Resume & Job Description Ingestion**: Upload drag-and-drop parser for candidate resumes (PDF/Docx) and job descriptions with skill graph extraction.
- 🎙️ **Live Interview Workspace**: Interactive exam interface featuring code editor input, text response area, countdown timer, and voice audio streaming support.
- 📋 **Diagnostic Reports & PDF Download**: Turn-by-turn answer evaluation, competency breakdowns, overall score rings, and server-side PDF report rendering via ReportLab.
- 📈 **Analytics & Benchmarks**: Visual score trends, category skill heatmaps, and peer benchmark comparison charts using Recharts.
- 🎓 **Career Roadmap & Learning Hub**: Skill gap analysis mapped to step-by-step career growth recommendations and weak-topic tag clusters.
- 🗄️ **Interview Session Archive**: History table with status filtering, session detail views, and side-by-side session comparison matrix.
- ⚡ **LangGraph Execution Visualization**: Visual representation of workflow stages, real-time node execution status, and log output.
- 🛰️ **Cluster Observability Dashboard**: Admin interface displaying node execution latencies, request throughput, and Prometheus system metrics.
- ⚙️ **Settings & Configuration**: Multi-tab settings panel for user profiles, theme toggling (Light/Dark/System), AI provider settings, and API key management.
- 🔌 **In-Process Model Context Protocol (MCP)**: Internal MCP server exposing 8 tools and 3 resources to standardize agent operations.

---

## System Architecture

```
                               ┌────────────────────────────────────────┐
                               │       React 19 Frontend App Shell      │
                               │  Vite • TypeScript • Tailwind • Query  │
                               └───────────────────┬────────────────────┘
                                                   │  HTTP REST / WebSockets / JWT
                                                   ▼
                               ┌────────────────────────────────────────┐
                               │           FastAPI API Gateway          │
                               │  Auth • Resumes • JDs • Interviews     │
                               └───────────────────┬────────────────────┘
                                                   │
                                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        LangGraph Workflow Engine (StateGraph)                          │
│                                                                                        │
│   [classify_candidate] ──> [generate_blueprint] ──> [personalize_question]             │
│                                                            │                           │
│                                                            ▼                           │
│                                                    [evaluate_answer] ───(loop/end)─────┘
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
┌───────────────────────────────────────┐     ┌───────────────────────────────────────┐
│     PostgreSQL 16 / SQLite Database   │     │        Redis 7 Pub/Sub & Cache        │
│  SQLAlchemy 2.0 • Alembic Migrations  │     │   WebSocket Connections & Cache       │
└───────────────────────────────────────┘     └───────────────────────────────────────┘
```

### Actual Data Flow

1. **User Request**: Candidate uploads a resume and job description via the React frontend.
2. **FastAPI Gateway**: Routes requests to `resume_service.py` and `jd_service.py` for text extraction and database storage.
3. **Interview Initialization**: `/api/v1/interviews/` instantiates an `Interview` record and triggers background plan generation.
4. **LangGraph Master Workflow**: `interview_service.py` executes `build_master_workflow()` from `app.graph.workflow_master`:
   - `classify_candidate`: Evaluates candidate tier and level using `CandidateClassifier`.
   - `generate_blueprint`: Creates sequence blueprint items via `BlueprintGenerator`.
   - `personalize_question`: Generates personalized interview questions via `PromptManager` and `Guardrails`.
   - `evaluate_answer`: Scores candidate responses and applies `DifficultyEngine` adaptations.
5. **State & Persistence**: Results are persisted to SQLAlchemy models (`Interview`, `InterviewQuestion`, `Evaluation`) and checked into LangGraph checkpointer memory.
6. **API Response & Visualization**: Scores and turn states are delivered via REST endpoints or live WebSocket streams to the frontend dashboard and report views.

---

## LangGraph Workflow & Agent Architecture

The application contains two graph definitions:

### 1. Master Execution Graph (`app.graph.workflow_master`)
This is the **active graph** executed by `interview_service.py` during live interview runs:

- **State Schema**: `InterviewState` (`GraphState`), a `TypedDict` containing identity keys, raw inputs, classification data, blueprint specs, question history, evaluations, and runtime flags.
- **Entry Point**: `classify_candidate`
- **Active Nodes**:
  - `classify_candidate`: Runs `CandidateClassifier` on resume and skill graph inputs.
  - `generate_blueprint`: Generates interview target items and category weightings.
  - `personalize_question`: Renders target question text using system prompts and PII masking.
  - `evaluate_answer`: Evaluates candidate answers and calculates dynamic difficulty adjustments.
- **Conditional Routing**: `route_next_step` checks total evaluated questions against blueprint targets to loop back to `personalize_question` or transition to `END`.

### 2. Multi-Agent Specification Graph (`app.graph.graph_builder`)
A 15-node topology specification defined in `graph_builder.py` for modular agent node testing:
- **Agents Defined**: `SupervisorAgent`, `ResumeAgent`, `JDAgent`, `ATSAgent`, `ProfileIntelligenceAgent`, `CompetencyMappingAgent`, `InterviewPlannerAgent`, `QuestionGeneratorHR`, `QuestionGeneratorTech`, `HRInterviewAgent`, `TechnicalInterviewAgent`, `EvaluationAgentHR`, `EvaluationAgentTech`, `CareerCoachAgent`, `ReportGeneratorAgent`.
- **Note**: Individual agent classes reside in `app/agents/`. Unit tests exercise these agent callables independently, while the runtime application uses the 4-node master graph.

---

## Model Context Protocol (MCP) Implementation

The repository implements an **in-process Model Context Protocol server** (`app.mcp.server.MCPServer`). It provides a centralized registry for tools, resources, and prompt templates used internally across agent implementations.

### Registered MCP Tools (`app/mcp/tools/`)

| Tool Name | File Path | Purpose | Input Parameters | Output |
|---|---|---|---|---|
| `parse_resume` | `app/mcp/tools/parse_resume.py` | Extracts text and skill entities from resume content | `raw_text: str` | `dict` (parsed skills & experience) |
| `parse_jd` | `app/mcp/tools/parse_jd.py` | Extracts requirements, target role, and skills from JD | `raw_text: str` | `dict` (required skills, role metadata) |
| `compute_ats_score` | `app/mcp/tools/compute_ats_score.py` | Calculates ATS match percentage and skill gaps | `resume_skills: list`, `jd_skills: list` | `dict` (match_percentage, missing_skills) |
| `map_skills` | `app/mcp/tools/map_skills.py` | Maps candidate skills to competency matrix categories | `skills: list`, `role: str` | `dict` (competency matrix mapping) |
| `score_answer_rubric` | `app/mcp/tools/score_answer_rubric.py` | Scores candidate answers against evaluation rubrics | `question: str`, `answer: str`, `rubric: dict` | `dict` (numerical score, feedback breakdown) |
| `generate_report_pdf` | `app/mcp/tools/generate_report_pdf.py` | Compiles evaluation metrics into PDF byte stream | `report_data: dict` | `bytes` (PDF document binary stream) |
| `persist_agent_output` | `app/mcp/tools/persist_agent_output.py` | Logs agent outputs to execution trace history | `agent_name: str`, `output_data: dict` | `dict` (persistence status & log ID) |
| `fetch_industry_standards` | `app/mcp/tools/fetch_industry_standards.py` | Retrieves benchmark standards for role categories | `role: str`, `seniority: str` | `dict` (benchmark criteria & targets) |

### Registered MCP Resources (`app/mcp/resources/`)

- `resource://industry-standards/{role}`: Returns baseline competency benchmarks for software engineering roles.
- `resource://company-competency-template/{company_tier}`: Returns evaluation rubric templates.
- `resource://question-bank/{category}`: Returns curated question seed banks.

*Note: The MCP implementation is an in-process Python registry used by internal backend modules, not an external network service endpoint.*

---

## Technology Stack

### **Frontend**
- **Core**: React 18/19, TypeScript 5.5, Vite 5
- **Styling**: Tailwind CSS, Custom Design System Tokens, Framer Motion
- **State & Data Fetching**: TanStack Query (React Query v5), React Hook Form, Zod, Zustand
- **Charts & Components**: Recharts, Lucide React, Radix UI primitives

### **Backend**
- **Framework**: FastAPI 0.109+, Uvicorn ASGI Server
- **ORM & Migrations**: SQLAlchemy 2.0 (Async), Alembic, Pydantic v2
- **Security**: Python-JOSE (JWT HS256), Passlib (BCrypt), Security Middleware
- **Agent Orchestration**: LangGraph StateGraph, LangChain Core
- **Speech Engine**: FasterWhisper (STT), Kokoro (TTS), SoundFile, NumPy
- **Document & PDF Processing**: PyMuPDF, PyPDF2, Python-Docx, ReportLab

### **Database & Infrastructure**
- **Database**: SQLite (Default local development), PostgreSQL 16 (Docker / Production config)
- **Caching & Streaming**: Redis 7 (Docker Compose configuration)
- **Proxy & Server**: Nginx
- **Containerization**: Docker, Docker Compose

### **Observability & Metrics**
- **Metrics**: Prometheus Client (`/metrics` endpoint exposing `GRAPH_EXECUTION_SECONDS`, `LLM_REQUESTS_TOTAL`)
- **Tracing**: OpenTelemetry FastAPI Instrumentation, LangSmith Tracing v2 support

---

## Project Structure

```
L2_Interview_Sage_AI/
├── backend/
│   ├── alembic/                 # Database migration scripts and env.py
│   ├── app/
│   │   ├── admin/               # Admin metrics and observability endpoints
│   │   ├── agents/              # 15 individual agent node implementations
│   │   ├── ai/                  # AI Gateway, Model Router, Token/Cost Trackers
│   │   ├── analytics/           # Deep-dive analytics computation services
│   │   ├── api/v1/routes/       # FastAPI REST & WebSocket routers (15 files)
│   │   ├── career/              # Learning Hub and career roadmap services
│   │   ├── core/                # Config, Database, Logging, Security, Telemetry
│   │   ├── dependencies/        # FastAPI Auth & DB session dependency injection
│   │   ├── evaluation/          # Evaluation models and rubric scoring
│   │   ├── graph/               # LangGraph StateGraph, state definition, master workflow
│   │   ├── kernel/              # AI Kernel (Prompt Manager, Guardrails, Model Router)
│   │   ├── mcp/                 # Model Context Protocol server, tools, and resources
│   │   ├── memory/              # Candidate long-term memory & semantic context
│   │   ├── middlewares/         # CORS, Security Headers, Request Context
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── prompts/             # System prompt registry and templates
│   │   ├── repositories/        # Database Access Objects (DAOs)
│   │   ├── schemas/             # Pydantic Request/Response schemas
│   │   ├── services/            # Business logic services (Interview, Resume, Report)
│   │   ├── speech/              # Speech-to-Text (STT) & Text-to-Speech (TTS) modules
│   │   ├── strategy/            # Dynamic Interview Strategy Engine (DISE)
│   │   ├── tests/               # Backend Pytest suite (58 test files)
│   │   ├── transcript/          # Turn-by-turn interview transcript processing
│   │   ├── utils/               # File utilities, text parsers, text clean helpers
│   │   └── websocket/           # WebSocket connection manager and handlers
│   ├── main.py                  # FastAPI application entry point
│   └── requirements.txt         # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                 # App Shell and top-level providers
│   │   ├── components/          # Shared UI primitives and layout blocks
│   │   ├── features/            # Domain feature modules (auth, dashboard, reports, etc.)
│   │   ├── hooks/               # Custom React & Query hooks
│   │   ├── pages/               # React Page views mapped to AppRoutes
│   │   ├── routes/              # React Router definitions (AppRoutes, ProtectedRoutes)
│   │   ├── services/            # Axios API Client (`apiClient.ts`) & WebSocket clients
│   │   ├── stores/              # Zustand state stores
│   │   └── types/               # TypeScript domain interfaces
│   ├── package.json             # Frontend dependencies and npm scripts
│   └── vite.config.ts           # Vite server proxy and build setup
├── docs/                        # Complete documentation suite (7 markdown guides)
├── infra/                       # Prometheus and deployment config templates
├── nginx/                       # Nginx reverse proxy configuration
├── docker-compose.yml           # Docker multi-container service definitions
├── .env.example                 # Environment variables template
└── .env.production.example      # Production environment configuration template
```

---

## API Reference

### Key API Endpoints (`/api/v1`)

| Method | Path | Auth Required | Description |
|---|---|:---:|---|
| `GET` | `/health` | No | System health probe (checks DB, MCP, subsystems) |
| `GET` | `/metrics` | No | Prometheus metrics endpoint |
| `POST` | `/api/v1/auth/register` | No | Register new user account |
| `POST` | `/api/v1/auth/login` | No | Authenticate user and receive JWT access token |
| `GET` | `/api/v1/auth/me` | Yes | Retrieve current authenticated user profile |
| `POST` | `/api/v1/resumes/` | Yes | Upload resume file (`multipart/form-data`) |
| `GET` | `/api/v1/resumes/{id}` | Yes | Retrieve parsed resume record |
| `POST` | `/api/v1/job-descriptions/` | Yes | Submit job description text/file |
| `POST` | `/api/v1/interviews/` | Yes | Initialize interview session and start plan generation |
| `GET` | `/api/v1/interviews/{id}` | Yes | Retrieve interview session details and question queue |
| `POST` | `/api/v1/answers/submit` | Yes | Submit candidate answer turn for scoring |
| `GET` | `/api/v1/reports/{interview_id}` | Yes | Fetch complete interview diagnostic report |
| `GET` | `/api/v1/reports/{interview_id}/pdf` | Yes | Stream generated ReportLab PDF document download |
| `GET` | `/api/v1/analytics/summary` | Yes | Retrieve user aggregate performance analytics |
| `GET` | `/api/v1/admin/agent-metrics` | Yes | Retrieve cluster node latencies and execution counts |
| `GET` | `/api/v1/memory/` | Yes | Query candidate long-term memory entries |
| `POST` | `/api/v1/voice/stt` | Yes | Transcribe audio snippet using STT service |
| `POST` | `/api/v1/voice/tts` | Yes | Synthesize text response using TTS service |
| `WS` | `/api/v1/ws/interview/{id}` | Yes | Live WebSocket stream for interview node execution |
| `WS` | `/api/v1/ws/audio/{id}` | Yes | Audio streaming WebSocket connection |

---

## Environment Configuration

Configuration is managed via Pydantic `BaseSettings` in [`backend/app/core/config.py`](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/backend/app/core/config.py), reading from `.env`:

```ini
# Application Setup
APP_NAME="InterviewSage AI"
ENVIRONMENT=development
DEBUG=true
HOST=127.0.0.1
PORT=8000

# Database (SQLite by default for local dev; PostgreSQL for Docker/prod)
DATABASE_URL=sqlite:///./interviewsage.db

# Security & Authentication (Required: high-entropy secret key)
SECRET_KEY=your_secure_secret_key_here_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# AI Provider Setup (ollama / local)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL_NAME=qwen3:instruct

# Speech Engine Setup
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
TTS_PROVIDER=kokoro

# CORS Origins (Comma-separated)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## Local Development

### Prerequisites
- **Python**: `3.10+`
- **Node.js**: `18.0+`
- **npm**: `9.0+`

### 1. Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Launch Uvicorn development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Backend REST API: `http://127.0.0.1:8000`
- Swagger OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup

```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

- Frontend App: `http://localhost:5173`

---

## Docker & Deployment

The repository includes a containerized multi-service setup defined in [`docker-compose.yml`](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docker-compose.yml):

```bash
# Copy environment template
cp .env.example .env

# Build and start services (Frontend, Backend, PostgreSQL 16, Redis 7)
docker-compose up -d --build
```

### Included Services:
- `frontend`: React SPA served via Nginx reverse proxy on port `80`.
- `backend`: FastAPI server on port `8000` (internal network).
- `postgres`: PostgreSQL 16 database on port `5432`.
- `redis`: Redis 7 cache and Pub/Sub store on port `6379`.
- `ollama`: Optional local LLM inference container (`docker-compose --profile with-ollama up -d`).

---

## Testing & Quality Assurance

The codebase contains **58 backend test files** under `backend/app/tests/` covering API routes, core services, LangGraph workflows, strategy engines, and MCP tools.

### Running Backend Pytest Suite

```bash
cd backend

# Run all test modules
pytest app/tests -v

# Run with test coverage output
pytest app/tests --cov=app --cov-report=term-missing
```

### Running Frontend Tests

```bash
cd frontend

# TypeScript type check
npm run type-check

# Run Vitest unit tests
npm run test
```

---

## Current Scope & System Limitations

To ensure factual alignment with the codebase, the following operational characteristics should be noted:

1. **Active Master Graph vs. Agent Stubs**: The production workflow executes the 4-node master graph (`classify_candidate` ➔ `generate_blueprint` ➔ `personalize_question` ➔ `evaluate_answer`). Individual agent classes in `app/agents/` are tested independently but are orchestrated in production via this master workflow.
2. **Local LLM & Mock Fallback Execution**: The AI Gateway communicates with a local Ollama instance (`http://localhost:11434`). If Ollama is unverified or offline, the gateway uses a structured local fallback response to ensure application resilience.
3. **In-Process MCP Server**: The MCP implementation is an in-process Python class (`MCPServer`) serving as an internal tool registry for backend agents, rather than an external stdio/JSON-RPC daemon.
4. **Local Audio Processing**: STT (`FasterWhisper`) and TTS (`Kokoro`) modules run locally. When native binaries (`faster-whisper`, `kokoro`) are uninstalled, fallback handlers generate simulated transcriptions and audio buffers.
5. **Database Configuration**: Local development defaults to SQLite (`sqlite:///./interviewsage.db`). PostgreSQL 16 is configured for containerized execution via Docker Compose.

---

## Documentation

Comprehensive technical documentation is available in the [`docs/`](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/) directory:

- 🏗️ [**Architecture Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/Architecture.md) — System design, graph topology, and state machine specification.
- 📡 [**API Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/APIGuide.md) — Endpoint index, request schemas, and authentication details.
- 🚀 [**Deployment Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/DeploymentGuide.md) — Nginx, Docker Compose, and environment setup.
- 💻 [**Developer Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/DeveloperGuide.md) — Code style, project structure, and testing standards.
- 🛠️ [**Setup Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/SetupGuide.md) — Step-by-step local development installation.
- 👤 [**User Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/UserGuide.md) — Application features and interview workspace walkthrough.
- 🔄 [**Workflow Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/WorkflowGuide.md) — Workflow execution stages and state transitions.

---

## License

Proprietary — **InterviewSage AI Platform**  
*All rights reserved.*
