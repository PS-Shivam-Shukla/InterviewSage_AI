# Architecture Guide

## System Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  React 18 + TypeScript (Vite :5173)                              │
│  TanStack Query · React Router · Tailwind CSS · Recharts         │
└──────────────────────────────┬──────────────────────────────────┘
                                │ REST + SSE  /api/v1
┌──────────────────────────────▼──────────────────────────────────┐
│  FastAPI :8000                                                    │
│  Routes → Controllers → Services → Repositories                  │
│  JWT auth · Pydantic validation · CORS · OpenAPI /docs           │
└──────────────────────────────┬──────────────────────────────────┘
                                │ invokes
┌──────────────────────────────▼──────────────────────────────────┐
│  LangGraph StateGraph[InterviewState]                             │
│  15 nodes · conditional edges · SQLite checkpointer              │
└──────────────────────────────┬──────────────────────────────────┘
                                │ dispatches to
┌──────────────────────────────▼──────────────────────────────────┐
│  12 Specialist AI Agents (base.py + per-agent modules)           │
│  Each: structured output · retry logic · MCP tool calls          │
└──────────────────────────────┬──────────────────────────────────┘
                                │ governed by
┌──────────────────────────────▼──────────────────────────────────┐
│  MCP Server (in-process)                                          │
│  7 tools · 3 resources · prompt registry · call log              │
└──────────────────────────────┬──────────────────────────────────┘
                                │ LangChain abstraction
┌──────────────────────────────▼──────────────────────────────────┐
│  LLM Layer  (primary + fallback, temperature per agent)          │
└──────────────────────────────┬──────────────────────────────────┘
                                │ repository pattern
┌──────────────────────────────▼──────────────────────────────────┐
│  SQLite  interviewsage.db  (Alembic migrations, FK enforced)     │
└─────────────────────────────────────────────────────────────────┘
```

## LangGraph Topology

```
START → supervisor → resume_agent → jd_agent → ats_agent
      → profile_intelligence_agent → competency_mapping_agent
      → interview_planner_agent
            ├─[hr_question_count>0]──► question_generator_hr
            │                              └► hr_interview_agent
            │                                    └► evaluation_agent_hr
            │                                          ├─[more HR]──► question_generator_hr (loop)
            │                                          └─[HR done]──► question_generator_tech
            └─[hr_question_count==0]─► question_generator_tech
                                            └► technical_interview_agent
                                                  └► evaluation_agent_tech
                                                        ├─[more tech]──► question_generator_tech (loop)
                                                        └─[tech done]──► career_coach_agent
                                                                              └► report_generator_agent → END
```

### Key design decisions

**Why LangGraph?** The interview loop requires genuine cycles (ask → answer → evaluate → ask again), conditional branching (HR-only, tech-only, combined), and pause/resume semantics. LangGraph's typed state machine provides all three with built-in checkpointing.

**Why separate question generators?** `question_generator_hr` and `question_generator_tech` are instances of the same `QuestionGeneratorAgent` class with `round_type="HR"` or `"TECHNICAL"`. Separate nodes allow each to have its own routing edge, keeping the conditional logic simple and explicit.

**Why stubs in Phase 5?** The graph is compiled once with all 15 nodes. Real agent callables are injected via `build_graph(resume_agent=..., ...)`. This allows the graph structure to be tested independently of agent logic.

## MCP Design

MCP (Model Context Protocol) decouples *what agents can do* from *how they do it*.

```
Agent code                      MCP Server
─────────────────               ──────────────────────────────
mcp_server.call_tool(           Tool Registry
  "compute_ats_score",           ├── parse_resume_pdf
  resume_skills=[...],           ├── parse_jd_text
  jd_required_skills=[...],      ├── compute_ats_score
)                                ├── fetch_industry_standards
                                 ├── score_answer_rubric
mcp_server.read_resource(        ├── persist_agent_output
  "resource://industry-          └── generate_report_pdf
   standards/backend-engineer"
)                               Resource Registry
                                 ├── resource://industry-standards/{role}
                                 ├── resource://competency-templates/{role}
                                 └── resource://question-bank/{role}/{difficulty}
```

Every call is appended to an internal call log surfaced in the Admin Dashboard.

## Database Schema

11 tables with full referential integrity:

```
users ──< resumes
      ──< job_descriptions
      ──< interviews ──── competency_matrices  (1:1)
                     ──── interview_plans       (1:1)
                     ──< interview_questions ──── interview_answers ──── evaluations  (1:1 each)
                     ──── interview_reports    (1:1)
                     ──< agent_logs
```

All JSON columns are stored as `TEXT` with Pydantic validation on read/write, making the PostgreSQL migration (swap `TEXT` → `JSONB`) trivial.

## InterviewState Fields

| Field | Writer | Notes |
|---|---|---|
| `interview_id` / `user_id` | Supervisor (init) | Identity |
| `resume_raw_text` / `jd_raw_text` | Service layer | Inputs |
| `resume_data` / `jd_data` | Resume/JD agents | Extracted |
| `ats_analysis` | ATS agent | Overlap score |
| `profile_summary` | Profile Intelligence agent | Seniority calibration |
| `competency_matrix` | Competency Mapping agent | Weights sum = 100 |
| `interview_plan` | Interview Planner agent | Q counts, duration |
| `current_question` | Question Generator | Active turn |
| `questions_asked` | HR/Tech agents | Reducer: append |
| `answers` | HR/Tech agents | Reducer: append |
| `evaluations` | Evaluation agent | Reducer: append |
| `coaching_plan` | Career Coach agent | Improvement plan |
| `final_report` | Report Generator | Compiled output |
| `pending_answer` | Service layer | Candidate's typed answer |
