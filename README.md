<div align="center">

# 🧠 InterviewSage AI

### **Production-Grade Enterprise AI Interview Simulation & Agentic Telemetry Platform**

*Powered by FastAPI, LangGraph Multi-Agent Orchestration, React 19, TypeScript, and Recharts Telemetry*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB.svg?style=for-the-badge&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_DAG-FF6F61.svg?style=for-the-badge)](https://www.langchain.com/langgraph)
[![TailwindCSS v4](https://img.shields.io/badge/TailwindCSS-v4.0-38B2AC.svg?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg?style=for-the-badge)](LICENSE)

</div>

---

## 🚀 Overview

**InterviewSage AI** is a state-of-the-art, full-stack AI interview simulation platform designed for candidates and enterprise engineering organizations. Driven by a 12-node **LangGraph directed acyclic graph (DAG)** of autonomous AI agents, the platform conducts personalized multi-round technical and behavioral interviews, analyzes resumes against job descriptions, evaluates candidate answers in real time with live telemetry, and generates PDF diagnostic reports.

---

## ✨ Key Features & Platform Capabilities

| Module | Feature Highlight | Description |
|---|---|---|
| 🔐 **Authentication & Security** | Split-Screen Auth & JWT | JWT session security, 409 conflict email checking, password strength meter, 2FA, and active session management. |
| 📊 **Command Dashboard** | Bento Grid Analytics | Glanceable welcome card, quick actions, 5 stat cards with trend deltas, latest report score ring, and activity stream. |
| 🎯 **4-Step Interview Wizard** | Resume & JD Ingestion | Drag-and-drop resume uploader with skill extraction, JD parser, experience level selector, and round configuration. |
| 🎙️ **Live Interview Exam Workspace** | Distraction-Free Exam UI | Top bar countdown timer, Rich Text editor, Monospace Code IDE, voice mic waveform tab, and live AI score bars. |
| 📋 **Diagnostic Reports** | Recharts Competency Radar | Comprehensive scorecard, ATS match %, percentile ranking, strength/growth callouts, transcript breakdown, and PDF download. |
| 📈 **Deep-Dive Analytics** | Multi-Tab Data Visualization | 5 analytical chart tabs mapping score trajectory, donut distributions, skills matrix heatmaps, and peer benchmarks. |
| 🎓 **Personalized Learning Hub** | Encouragement Bento Grid | Recommended course cards carousel, weak-topic tags, vertical step roadmap, and circular weekly goal ring widget. |
| 🗄️ **Interview Archive** | Multi-Session Compare Mode | Searchable table/grid archive, filter popovers, delete confirmation dialogs, and side-by-side comparison modal. |
| ⚡ **AI Multi-Agent Workflow** | LangGraph Tracing | Real-time DAG node pipeline execution view, Framer Motion traveling pulse connectors, and live monospace log stream. |
| 🛰️ **Cluster Observability** | Datadog-Style Telemetry | Observability dashboard for 9 agent nodes featuring mini Recharts latency sparklines, Gantt execution timeline, and load heatmap. |
| ⚙️ **Enterprise Settings** | URL-Persisted Section Tabs | 6 URL-synced tabs (`/settings?tab=...`), segmented theme switcher, AI model provider configuration, and one-time API key generator. |

---

## 🏗️ System Architecture & Multi-Agent DAG Topology

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 React 19 App Shell (UI)               │
                  │   Vite • TypeScript • Tailwind v4 • TanStack Query    │
                  └──────────────────────────┬─────────────────────────────┘
                                             │  HTTP / REST / JWT Bearer
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │                 FastAPI API Gateway                    │
                  │     Auth • Users • Resumes • JDs • Interviews • Admin   │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                                             ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                           LangGraph Multi-Agent Engine DAG                             │
  │                                                                                        │
  │   [Resume Upload] ──> [Resume Agent] ──> [JD Agent] ──> [ATS Agent]                     │
  │                                                                 │                      │
  │   [Planner Agent] <── [Profile Agent] <───────────────────────────┘                      │
  │          │                                                                             │
  │          └──> [Supervisor Router] ──> [HR Round Agent] ──> [Evaluation Agent]           │
  │                                   ──> [Tech Round Agent] ──> [Evaluation Agent]        │
  │                                                                 │                      │
  │   [Final Report] <── [Career Coach Agent] <─────────────────────┘                      │
  └──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │               SQLite Database & Alembic                │
                  │          `interviewsage.db` • SQLAlchemy ORM           │
                  └────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack Matrix

### **Frontend**
- **Core Framework**: React 19, TypeScript (Strict mode), Vite
- **Styling & UI**: Tailwind CSS v4, Vanilla CSS Design System tokens, Framer Motion animations
- **State Management & Async Data**: TanStack Query (React Query v5), React Hook Form + Zod validation
- **Data Visualization**: Recharts (Radar, Line, Bar, Donut, Composed, RadialBar)
- **Icons & Theme**: Lucide Icons, ThemeProvider (Light / Dark / System)

### **Backend**
- **API Framework**: FastAPI, Uvicorn (ASGI)
- **ORM & Migrations**: SQLAlchemy 2.0, Alembic, SQLite
- **Security & Authentication**: Python-JOSE (JWT), Passlib (Bcrypt), Python-Multipart
- **Agentic Orchestration**: LangGraph StateGraph, LangChain Structured Output, OpenAI GPT-4 API
- **Document Processing**: PyPDF2, Python-Docx, ReportLab (PDF Generation)

---

## 📁 Repository Structure

```
L2_Interview_Sage_AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/       # FastAPI Endpoint Routers (Auth, Interviews, Resumes, etc.)
│   │   ├── core/                # Database setup, App Configuration, CORS, Security
│   │   ├── dependencies/        # JWT Authentication dependencies & Current User inject
│   │   ├── graph/               # LangGraph StateGraph, InterviewState reducers, DAG Builder
│   │   ├── models/              # SQLAlchemy Database Models
│   │   ├── schemas/             # Pydantic Request/Response Models
│   │   └── services/            # Business Logic Services & LLM Agent Callables
│   ├── alembic/                 # Database Migrations
│   ├── uploads/                 # Storage for uploaded resume & JD files
│   ├── requirements.txt         # Backend Python Dependencies
│   └── main.py                  # Uvicorn FastAPI Server Entry Point
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # App Shell, Router, Layout, ThemeProvider
│   │   ├── components/ui/       # Reusable UI Primitives (Button, Card, Badge, Modal, etc.)
│   │   ├── components/shared/   # Shared Layout Components (Header, SkeletonBlock, ErrorState)
│   │   ├── features/            # Feature Domain Pages & Components
│   │   │   ├── auth/            # Sign In & Register Pages with Split-Screen Shell
│   │   │   ├── dashboard/       # Bento Grid Overview Dashboard
│   │   │   ├── new-interview/   # 4-Step Interview Wizard
│   │   │   ├── live-interview/  # Distraction-Free Exam Workspace
│   │   │   ├── reports/         # Performance Diagnostic Report
│   │   │   ├── analytics/       # Deep-Dive Analytics & Charts
│   │   │   ├── learning-hub/    # Personalized Learning Hub
│   │   │   ├── interview-history/ # Archive & Side-by-Side Comparison
│   │   │   ├── ai-workflow/     # LangGraph Live Execution Tracing
│   │   │   ├── agent-monitoring/# Cluster Observability & Heatmaps
│   │   │   └── settings/        # Enterprise Settings & API Key Generator
│   │   ├── hooks/               # TanStack Query Custom Hooks
│   │   ├── services/            # Centralized API Clients (`apiClient.ts`)
│   │   └── types/               # TypeScript Domain Interfaces
│   ├── package.json             # Frontend Dependencies & Scripts
│   └── vite.config.ts           # Vite Build & Proxy Configuration
│
└── docs/                        # Complete Architecture & API Documentation
```

---

## ⚡ Quick Start & Local Setup

### **Prerequisites**
- **Python**: `3.10+`
- **Node.js**: `18.0+`
- **npm**: `9.0+`

---

### **1. Backend Setup (FastAPI)**

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server (option 1: inside backend folder)
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Run server (option 2: from root project folder)
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

> **FastAPI Server**: `http://127.0.0.1:8000`  
> **Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs`

---

### **2. Frontend Setup (React 19 + Vite)**

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Start Vite development server
npm run dev
```

> **Frontend Dashboard**: `http://localhost:5173`

---

## 🧪 Testing & Code Quality

For the complete command reference, see the dedicated [**`TESTING.md`**](TESTING.md) guide.

### **Quick Command Summary**

```bash
# Backend Test Suite (148 Pytest items)
cd backend && pytest app/tests

# Frontend Type Check & Unit Tests
cd frontend && npm run type-check && npm run test && npm run build
```

---

## 🌐 API Endpoint Index

| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `POST` | `/api/v1/auth/register` | Register a new user account | ❌ |
| `POST` | `/api/v1/auth/login` | Authenticate user & receive JWT bearer token | ❌ |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile | ✅ |
| `POST` | `/api/v1/resumes/` | Upload resume file (`multipart/form-data`) | ✅ |
| `POST` | `/api/v1/job-descriptions/` | Submit job description text / PDF | ✅ |
| `POST` | `/api/v1/interviews/` | Initialize new interview session with LangGraph DAG | ✅ |
| `GET` | `/api/v1/interviews/{id}` | Fetch current interview session status | ✅ |
| `POST` | `/api/v1/interviews/{id}/answers` | Submit candidate answer turn | ✅ |
| `GET` | `/api/v1/reports/{interview_id}` | Retrieve final interview diagnostic report | ✅ |
| `GET` | `/api/v1/reports/{interview_id}/pdf` | Stream PDF report download attachment | ✅ |
| `GET` | `/api/v1/analytics/summary` | Fetch user analytics summary & score trend | ✅ |
| `GET` | `/api/v1/admin/agent-metrics` | Fetch cluster agent observability telemetry | ✅ |

## 📚 Documentation & Reference Guides

- [**`BUILD_PROMPTS.md`**](BUILD_PROMPTS.md): Complete 14-prompt modular build specification & prompt suite.
- [**`TESTING.md`**](TESTING.md): Comprehensive testing guide & command reference (Pytest & Vitest).
- [**`docs/`**](docs/): In-depth system architecture, API specification, and developer guides.

---

## 🔒 Security & Best Practices

- **JWT Authentication**: Passlib bcrypt password hashing with HS256 JWT tokens.
- **CORS Protection**: Explicit origins middleware configured via environment variables.
- **Offline Resilience**: Service modules feature interceptor-level fallback handling to keep the UI resilient during offline development.
- **Form Integrity**: Client-side Zod validation mirrors backend Pydantic models to prevent invalid requests.

---

## 🛡️ Native Production Deployment Guide

InterviewSage AI is designed for native production execution without container abstractions.

### **1. Backend Production Startup (Uvicorn / FastAPI)**

```bash
# 1. Environment Setup
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Configure Production Secrets
cp ../.env.production.example .env.production
# Edit .env.production with your secure SECRET_KEY, PostgreSQL DATABASE_URL, and CORS_ORIGINS

# 3. Launch Native ASGI Server
export ENVIRONMENT=production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **2. Frontend Production Build & Hosting**

```bash
# 1. Install & Build
cd frontend
npm install
npm run build

# 2. Production Assets
# Serve static assets from dist/ via Nginx / Cloudflare Pages / Caddy
```

### **3. Database Configuration & Security**
- **Development**: SQLite (`sqlite:///./interviewsage.db`) for lightweight zero-config local testing.
- **Production**: PostgreSQL (`postgresql://user:password@host:5432/interviewsage_prod`) for ACID compliance and connection pooling.
- **Security Headers**: Automatic HTTP middleware applies `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-XSS-Protection`.

---

## 📄 License

Proprietary — **InterviewSage AI Platform**  
*All rights reserved. Designed and developed for enterprise agentic interview simulations.*
