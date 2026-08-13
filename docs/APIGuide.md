# API Guide

Base URL: `http://127.0.0.1:8000/api/v1`

Interactive docs: `http://127.0.0.1:8000/docs`

All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

All error responses follow:
```json
{ "detail": "Human-readable message" }
```

---

## Authentication

### POST /auth/register
Create a new account.

**Request:**
```json
{ "email": "jane@example.com", "password": "mypassword", "full_name": "Jane Smith" }
```

**Response 201:**
```json
{ "access_token": "...", "token_type": "bearer", "user": { "id": "...", "email": "...", "full_name": "...", "created_at": "..." } }
```

**Error 409:** Email already registered.

---

### POST /auth/login
Authenticate and receive a token.

**Request:**
```json
{ "email": "jane@example.com", "password": "mypassword" }
```

**Response 200:** Same shape as `/auth/register`.

**Error 401:** Invalid credentials.

---

### GET /auth/me *(auth required)*
Return the currently authenticated user.

---

## Resumes

### POST /resumes/
Upload a resume file (PDF, DOCX, TXT). Multipart form.

**Response 201:** `Resume` object with extracted `parsed_skills`, `seniority_signal`.

---

### GET /resumes/{id}
Retrieve a previously uploaded resume.

---

## Job Descriptions

### POST /job-descriptions/
Submit a job description.

**Request:**
```json
{ "raw_text": "...", "target_role": "Senior Backend Engineer", "company_name": "Acme" }
```

**Response 201:** `JobDescription` object.

---

## Interviews

### POST /interviews/
Start a new interview (kicks off the LangGraph planning pipeline).

**Request:**
```json
{ "resume_id": "...", "jd_id": "..." }
```

**Response 200:** `Interview` object with `status: "PLANNING"`.

---

### GET /interviews/{id}
Fetch current interview status.

---

### GET /interviews/{id}/plan
Fetch the generated interview plan (HR count, tech count, duration).

---

### POST /interviews/{id}/answers *(SSE stream)*
Submit the candidate's answer. Returns a `text/event-stream`.

**Request:**
```json
{ "answer_text": "I built a distributed payment system using..." }
```

**Stream events:**
```
data: {"type": "ack", "message": "Answer received, processing…"}
data: {"type": "evaluation", "data": {"score": 8, "feedback": "...", ...}}
data: {"type": "token", "content": "Walk "}
data: {"type": "token", "content": "me "}
data: {"type": "done", "interview_complete": false}
```

---

### POST /interviews/{id}/pause
Pause an in-progress interview.

### POST /interviews/{id}/resume
Resume a paused interview.

### GET /interviews/{id}/evaluations
Fetch all evaluations so far.

### GET /interviews/{id}/report
Fetch the final report (only available when `status == COMPLETED`).

### GET /interviews/{id}/report/pdf
Download the report as a file.

### GET /interviews
List all interviews for the current user.

---

## Analytics

### GET /analytics/summary
Dashboard summary statistics.

**Response:**
```json
{
  "summary": {
    "total_interviews": 5,
    "average_score": 7.4,
    "completion_rate": 0.8,
    "weak_competencies": ["System Design"],
    "score_trend": [{"date": "Aug 01", "score": 7}]
  }
}
```

### GET /analytics/trends
Score data points for the trend line.

### GET /analytics/competencies
Aggregated per-competency averages across all interviews.

---

## Admin

### GET /admin/agent-metrics *(admin only)*
Agent health metrics from `AGENT_LOG`.

**Response:**
```json
{
  "metrics": [
    { "agent_name": "ResumeAgent", "success_rate": 0.98, "avg_latency_ms": 320, "retry_rate": 0.02, "total_calls": 50 }
  ]
}
```

**Error 403:** Non-admin user.

---

## Users

### PATCH /users/{id}
Update profile (name only in v1).

### GET /users/{id}/export
Export all user data as JSON.
