<div align="center">

# 🧠 InterviewSage AI

**An AI interview simulation and telemetry platform built with FastAPI, LangGraph, React 19, TypeScript, and OpenTelemetry.**

<br />

![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)
![React 19](https://img.shields.io/badge/React-19.0-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg?style=for-the-badge&logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-FF6F61.svg?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)

<br />

[Overview](#-overview) • [Problem & Solution](#-problem--solution) • [Key Features](#%EF%B8%8F-key-features) • [Tech Stack](#-technology-stack-matrix) • [Architecture](#%EF%B8%8F-system-architecture) • [LangGraph Workflow](#-langgraph-workflow--agent-architecture) • [MCP Server](#-model-context-protocol-mcp-implementation) • [API](#-api-reference) • [Documentation](#-documentation)

</div>

---

## 📌 Overview

**InterviewSage AI** is a full-stack application designed to automate and analyze technical and behavioral interview workflows. The system ingests candidate resumes and job descriptions, classifies candidate experience levels, builds structured evaluation plans via a **Dynamic Interview Strategy Engine (DISE)**, executes multi-turn question-and-answer sessions via a **LangGraph StateGraph** workflow, scores answers using an **AI Kernel**, and renders diagnostic PDF scorecards.

The repository comprises a FastAPI backend server, a React 19 single-page application (SPA), an in-process **Model Context Protocol (MCP)** server, local Speech-to-Text (STT) and Text-to-Speech (TTS) voice modules, and containerized deployment definitions via Docker Compose.

---

## 🎯 Problem & Solution

### The Challenge
Technical and behavioral candidate evaluations often suffer from inconsistent scoring criteria, manual overhead in matching resume experience against job requirements, and lack of structured telemetry during practice sessions.

### The Implementation
InterviewSage AI addresses these issues through:
1. 📄 **Automated Document Extraction**: Extracting structured skill sets and requirements from uploaded PDF/Docx files.
2. 🎯 **Dynamic Strategy Engine (DISE)**: Classifying candidate experience levels (Junior, Mid, Senior, Lead, Principal) to build targeted evaluation blueprints.
3. ⚡ **LangGraph StateGraph Engine**: Managing interview turn state, question rendering, and scoring state machines.
4. 🛡️ **AI Kernel Resiliency**: Enforcing system prompt versioning, PII masking, injection scanning, and local model routing.
5. 📊 **Observability & Metrics**: Exposing Prometheus metrics (`GRAPH_EXECUTION_SECONDS`, `LLM_REQUESTS_TOTAL`) and OpenTelemetry tracing hooks.
6. 🔌 **In-Process MCP Registry**: Standardizing internal agent tool invocations through a structured registry.

---

## ⚙️ Key Features

| Module | Feature | Implementation Details |
|---|---|---|
| 🔐 **Authentication** | JWT & Session Security | HS256 JWT tokens, BCrypt password hashing, session context tracking, and security headers (`nosniff`, `DENY`, `strict-origin-when-cross-origin`). |
| 📊 **Dashboard** | Overview Command Center | High-level metrics display, active interview session status, score ring visualizer, and quick launch buttons. |
| 🎯 **Document Setup** | Resume & JD Parsing | Drag-and-drop file uploader (PDF/Docx) with skill extraction and job requirement parsing. |
| 🎙️ **Exam Workspace** | Interactive Exam IDE | Monospace code input area, rich-text workspace, countdown timer, and local STT/TTS audio streaming integration. |
| 📋 **Reports & PDF** | Diagnostic Scorecard | Per-turn evaluation breakdown, ATS match calculation, competency radar, and ReportLab PDF document stream. |
| 📈 **Analytics** | Benchmarks & Trends | Recharts visualization tabs displaying score trajectories, category heatmaps, and peer percentile comparisons. |
| 🎓 **Learning Hub** | Skill Gap Roadmap | Weak-topic tag clusters, vertical step-by-step learning roadmap, and course recommendations. |
| 🗄️ **Interview Archive** | History & Comparison | Searchable session table, status filter controls, session detail drawers, and side-by-side comparison modal. |
| ⚡ **Workflow Visualizer** | LangGraph Node Tracing | Execution stage indicator, live node state display, and monospace execution logs. |
| 🛰️ **Observability** | Cluster Metrics Panel | Admin dashboard displaying node execution latencies, throughput counters, and system metrics. |
| ⚙️ **Settings** | Configuration Management | Multi-tab settings panel for user preferences, theme selection (Light/Dark/System), and API key management. |
| 🔌 **MCP Server** | In-Process Registry | Centralized Python registry exposing 8 tools and 3 resources for internal agent invocations. |

---

## 🛠️ Technology Stack Matrix

| Category | Tech Stack Badges | Implemented Stack Details |
|---|---|---|
| 💻 **Frontend Core** | ![React](https://img.shields.io/badge/React_19-61DAFB?style=flat-square&logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript_5.5-3178C6?style=flat-square&logo=typescript&logoColor=white) ![Vite](https://img.shields.io/badge/Vite_5-646CFF?style=flat-square&logo=vite&logoColor=white) | React 19 SPA, TypeScript 5.5, Vite 5 build tool |
| 🎨 **UI & Styling** | ![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white) ![Framer](https://img.shields.io/badge/Framer_Motion-0055FF?style=flat-square&logo=framer&logoColor=white) ![Radix](https://img.shields.io/badge/Radix_UI-161618?style=flat-square&logo=radixui&logoColor=white) | Tailwind CSS tokens, Framer Motion animations, Radix UI primitives |
| 🔄 **State & Query** | ![TanStack](https://img.shields.io/badge/TanStack_Query_v5-FF4154?style=flat-square&logo=reactquery&logoColor=white) ![Zod](https://img.shields.io/badge/Zod-3E67B1?style=flat-square&logo=zod&logoColor=white) | TanStack Query v5, React Hook Form, Zod validation, Zustand |
| 📊 **Visualization** | ![Recharts](https://img.shields.io/badge/Recharts-22B5BF?style=flat-square) ![Lucide](https://img.shields.io/badge/Lucide_Icons-F56565?style=flat-square) | Recharts (Radar, Line, Bar, Composed, Donut), Lucide Icons |
| ⚡ **Backend Engine** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) ![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=flat-square&logo=python&logoColor=white) ![Pydantic](https://img.shields.io/badge/Pydantic_v2-E92063?style=flat-square&logo=pydantic&logoColor=white) | FastAPI 0.109+, Uvicorn ASGI Server, Pydantic v2 schemas |
| 🤖 **Agentic Orchestration** | ![LangGraph](https://img.shields.io/badge/LangGraph-FF6F61?style=flat-square) ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white) | LangGraph StateGraph engine, LangChain Core |
| 💾 **Database & Storage** | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat-square) | SQLite (local default), PostgreSQL 16 (Docker), SQLAlchemy 2.0 Async, Alembic |
| 🔴 **Caching & Pub/Sub** | ![Redis](https://img.shields.io/badge/Redis_7-DC382D?style=flat-square&logo=redis&logoColor=white) | Redis 7 cache & Pub/Sub (Docker Compose configuration) |
| 🎙️ **Voice & Audio** | ![Whisper](https://img.shields.io/badge/FasterWhisper_STT-000000?style=flat-square) ![Kokoro](https://img.shields.io/badge/Kokoro_TTS-FF9900?style=flat-square) | FasterWhisper STT, Kokoro TTS neural synthesis, SoundFile, NumPy |
| 📄 **Document & PDF** | ![PyMuPDF](https://img.shields.io/badge/PyMuPDF-3776AB?style=flat-square) ![ReportLab](https://img.shields.io/badge/ReportLab_PDF-CC0000?style=flat-square) | PyMuPDF, PyPDF2, Python-Docx, ReportLab PDF rendering engine |
| 🐳 **Infrastructure** | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) ![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white) | Docker, Docker Compose multi-container orchestration, Nginx proxy |
| 🛰️ **Observability** | ![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat-square&logo=prometheus&logoColor=white) ![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-000000?style=flat-square&logo=opentelemetry&logoColor=white) | Prometheus (`/metrics`), OpenTelemetry FastAPI instrumentation, LangSmith v2 |

---

## 🏗️ System Architecture

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

### Execution Flow

1. **Upload Phase**: Candidate uploads a resume and job description via the React frontend. `resume_service.py` and `jd_service.py` extract text and store records via SQLAlchemy.
2. **Session Initialization**: `/api/v1/interviews/` creates an `Interview` record and triggers background plan generation.
3. **LangGraph Master Workflow Execution**: `interview_service.py` invokes `build_master_workflow()` from `app.graph.workflow_master`:
   - `classify_candidate`: Evaluates candidate tier and level using `CandidateClassifier`.
   - `generate_blueprint`: Constructs blueprint sequence items using `BlueprintGenerator`.
   - `personalize_question`: Generates target question text using `PromptManager` and `Guardrails`.
   - `evaluate_answer`: Evaluates responses and applies `DifficultyEngine` adaptations.
4. **State Persistence**: State updates persist to database models (`Interview`, `InterviewQuestion`, `Evaluation`) and checkpointer memory.
5. **Client Response**: Scores and session states are returned via REST endpoints or WebSocket connections to the frontend SPA.

---

## ⚡ LangGraph Workflow & Agent Architecture

The application contains two graph definitions:

### 1. Master Execution Graph (`app.graph.workflow_master`)
This is the **active workflow** invoked by `interview_service.py` during interview execution:

- **State Schema**: `InterviewState` (`GraphState`), a `TypedDict` containing identity identifiers, raw text inputs, classification metrics, blueprint definitions, question logs, evaluations, and execution flags.
- **Entry Point**: `classify_candidate`
- **Active Nodes**:
  - `classify_candidate`: Runs `CandidateClassifier` on candidate inputs.
  - `generate_blueprint`: Generates interview target items and category allocations.
  - `personalize_question`: Formats question text with PII masking.
  - `evaluate_answer`: Evaluates responses and adjusts next turn difficulty.
- **Conditional Edge**: `route_next_step` checks evaluated question count against blueprint target to loop back to `personalize_question` or finish at `END`.

### 2. Multi-Agent Specification Graph (`app.graph.graph_builder`)
A 15-node topology specification defined in `graph_builder.py` for modular agent node testing:
- **Defined Agents**: `SupervisorAgent`, `ResumeAgent`, `JDAgent`, `ATSAgent`, `ProfileIntelligenceAgent`, `CompetencyMappingAgent`, `InterviewPlannerAgent`, `QuestionGeneratorHR`, `QuestionGeneratorTech`, `HRInterviewAgent`, `TechnicalInterviewAgent`, `EvaluationAgentHR`, `EvaluationAgentTech`, `CareerCoachAgent`, `ReportGeneratorAgent`.
- **Implementation Note**: Individual agent classes reside in `app/agents/`. Unit tests verify these callables independently, while runtime execution uses the 4-node master graph.

---

## 🔌 Model Context Protocol (MCP) Implementation

InterviewSage AI includes an **in-process Model Context Protocol server** (`app.mcp.server.MCPServer`) that acts as a centralized tool and resource registry for backend agent operations.

### Registered Tools (`app/mcp/tools/`)

| Tool Name | Source File | Description | Parameters | Output |
|---|---|---|---|---|
| `parse_resume` | `app/mcp/tools/parse_resume.py` | Extracts text and skill structures from resume content | `raw_text: str` | `dict` (parsed skills & experience) |
| `parse_jd` | `app/mcp/tools/parse_jd.py` | Extracts metadata, role targets, and required skills | `raw_text: str` | `dict` (required skills, metadata) |
| `compute_ats_score` | `app/mcp/tools/compute_ats_score.py` | Calculates ATS match percentage and skill gaps | `resume_skills: list`, `jd_skills: list` | `dict` (match_percentage, missing_skills) |
| `map_skills` | `app/mcp/tools/map_skills.py` | Maps candidate skills to competency categories | `skills: list`, `role: str` | `dict` (competency matrix mapping) |
| `score_answer_rubric` | `app/mcp/tools/score_answer_rubric.py` | Scores candidate answers against evaluation rubrics | `question: str`, `answer: str`, `rubric: dict` | `dict` (numerical score, feedback) |
| `generate_report_pdf` | `app/mcp/tools/generate_report_pdf.py` | Compiles evaluation metrics into PDF byte stream | `report_data: dict` | `bytes` (PDF binary stream) |
| `persist_agent_output` | `app/mcp/tools/persist_agent_output.py` | Logs agent outputs to execution trace history | `agent_name: str`, `output_data: dict` | `dict` (status & log ID) |
| `fetch_industry_standards` | `app/mcp/tools/fetch_industry_standards.py` | Retrieves benchmark standards for role categories | `role: str`, `seniority: str` | `dict` (benchmark criteria & targets) |

### Registered Resources (`app/mcp/resources/`)

- `resource://industry-standards/{role}`: Benchmark standards for software engineering roles.
- `resource://company-competency-template/{company_tier}`: Competency evaluation rubrics.
- `resource://question-bank/{category}`: Question seed banks.

> [!NOTE]
> The MCP implementation is an internal in-process Python registry used by backend modules, rather than an external network daemon.

---

## 📁 Project Structure

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

## 🌐 API Reference

### Core Endpoints (`/api/v1`)

| Method | Endpoint | Auth | Description |
|---|---|:---:|---|
| `GET` | `/health` | No | System health probe (checks DB, MCP, subsystems) |
| `GET` | `/metrics` | No | Prometheus metrics endpoint |
| `POST` | `/api/v1/auth/register` | No | Register a new user account |
| `POST` | `/api/v1/auth/login` | No | Authenticate user and receive JWT access token |
| `GET` | `/api/v1/auth/me` | Yes | Retrieve current authenticated user profile |
| `POST` | `/api/v1/resumes/` | Yes | Upload resume file (`multipart/form-data`) |
| `GET` | `/api/v1/resumes/{id}` | Yes | Retrieve parsed resume record |
| `POST` | `/api/v1/job-descriptions/` | Yes | Submit job description text/file |
| `POST` | `/api/v1/interviews/` | Yes | Initialize interview session and generate plan |
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

## 💻 Local Development

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

## 🐳 Docker Setup

Containerized deployment definitions are provided in [`docker-compose.yml`](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docker-compose.yml):

```bash
# Copy environment template
cp .env.example .env

# Build and start services (Frontend, Backend, PostgreSQL 16, Redis 7)
docker-compose up -d --build
```

### Services Included:
- `frontend`: React SPA served via Nginx reverse proxy on port `80`.
- `backend`: FastAPI server on port `8000` (internal network).
- `postgres`: PostgreSQL 16 database on port `5432`.
- `redis`: Redis 7 cache and Pub/Sub store on port `6379`.
- `ollama`: Optional local LLM container (`docker-compose --profile with-ollama up -d`).

---

## 🧪 Testing & Quality Assurance

The repository contains **58 backend test files** under `backend/app/tests/` covering API routes, core services, LangGraph workflows, strategy engines, and MCP tools.

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

## 🔍 System Scope & Limitations

> [!IMPORTANT]
> To ensure operational accuracy, note the following implementation specifics:

1. **Active Master Graph vs. Agent Stubs**: The production workflow executes the 4-node master graph (`classify_candidate` ➔ `generate_blueprint` ➔ `personalize_question` ➔ `evaluate_answer`). Individual agent classes in `app/agents/` are tested independently but are orchestrated in production via this master workflow.
2. **Local LLM & Mock Fallback Execution**: The AI Gateway connects to a local Ollama instance (`http://localhost:11434`). If Ollama is unverified or offline, the gateway uses a local fallback response to maintain session continuity.
3. **In-Process MCP Server**: The MCP implementation is an in-process Python class (`MCPServer`) serving as an internal tool registry for backend agents, rather than an external stdio/JSON-RPC daemon.
4. **Local Audio Processing**: STT (`FasterWhisper`) and TTS (`Kokoro`) modules run locally. When native binaries (`faster-whisper`, `kokoro`) are uninstalled, fallback handlers generate simulated transcriptions and audio buffers.
5. **Database Configuration**: Local development defaults to SQLite (`sqlite:///./interviewsage.db`). PostgreSQL 16 is configured for containerized execution via Docker Compose.

---

## 📚 Documentation

Detailed technical documentation is available in the [`docs/`](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/) directory:

- 🏗️ [**Architecture Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/Architecture.md) — System design, graph topology, and state machine specifications.
- 📡 [**API Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/APIGuide.md) — Endpoint index, request schemas, and authentication details.
- 🚀 [**Deployment Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/DeploymentGuide.md) — Nginx, Docker Compose, and environment setup.
- 💻 [**Developer Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/DeveloperGuide.md) — Code style, project structure, and testing standards.
- 🛠️ [**Setup Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/SetupGuide.md) — Local development installation steps.
- 👤 [**User Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/UserGuide.md) — Feature walkthrough and candidate workflow.
- 🔄 [**Workflow Guide**](file:///c:/Users/ShivamShukla/My_Workspace/L2_Interview_Sage_AI/docs/WorkflowGuide.md) — Workflow execution stages and state transitions.

---

## 📄 License

Proprietary — **InterviewSage AI Platform**  
*All rights reserved.*
