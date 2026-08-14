"""
MCP package — bootstraps and exports the singleton MCP server
with all tools and resources registered (Phase 5).
"""

from app.mcp.resources import (
    competency_templates_handler,
    industry_standards_handler,
    question_bank_handler,
)
from app.mcp.server import mcp_server
from app.mcp.tools import (
    compute_ats_score,
    fetch_industry_standards,
    generate_report_pdf,
    map_skills,
    parse_jd_text,
    parse_resume_pdf,
    persist_agent_output,
    score_answer_rubric,
)

# ── Register all v1 tools ────────────────────────────────────

mcp_server.register_tool(
    name="parse_resume_pdf",
    description="Extract and clean text from a resume PDF, DOCX, or TXT file",
    parameters={
        "file_path": {"type": "string", "description": "Absolute path to the resume file"},
    },
    handler=parse_resume_pdf,
    required_params=["file_path"],
)

mcp_server.register_tool(
    name="parse_jd_text",
    description="Normalize and structurally pre-process raw job description text",
    parameters={
        "raw_text": {"type": "string", "description": "Raw job description text"},
    },
    handler=parse_jd_text,
    required_params=["raw_text"],
)

mcp_server.register_tool(
    name="compute_ats_score",
    description="Compute keyword and skill overlap between a resume and JD",
    parameters={
        "resume_skills": {"type": "array", "description": "Skills from resume"},
        "jd_required_skills": {"type": "array", "description": "Required skills from JD"},
        "resume_text": {"type": "string", "description": "Full resume text (optional)"},
        "jd_text": {"type": "string", "description": "Full JD text (optional)"},
    },
    handler=compute_ats_score,
    required_params=["resume_skills", "jd_required_skills"],
)

mcp_server.register_tool(
    name="map_skills",
    description=(
        "Full skill matrix analysis: matched skills, missing skills, ATS score, "
        "strengths, weaknesses, and interview focus areas"
    ),
    parameters={
        "resume_skills": {"type": "array", "description": "Skills extracted from resume"},
        "jd_required_skills": {"type": "array", "description": "Mandatory JD skills"},
        "jd_preferred_skills": {"type": "array", "description": "Preferred JD skills (optional)"},
        "resume_text": {"type": "string", "description": "Full resume text for coverage analysis"},
        "jd_text": {"type": "string", "description": "Full JD text for coverage analysis"},
    },
    handler=map_skills,
    required_params=["resume_skills", "jd_required_skills"],
)

mcp_server.register_tool(
    name="fetch_industry_standards",
    description="Fetch industry competency benchmarks for a given role",
    parameters={
        "role": {"type": "string", "description": "Target job role / title"},
    },
    handler=fetch_industry_standards,
    required_params=["role"],
)

mcp_server.register_tool(
    name="score_answer_rubric",
    description="Return rubric schema or evaluate candidate answer against rubric anchors",
    parameters={
        "question_type": {"type": "string", "description": "behavioral | fundamentals | advanced | system_design"},
        "seniority_level": {"type": "string", "description": "JUNIOR | MID | SENIOR"},
        "answer_text": {"type": "string", "description": "Candidate answer text (optional)"},
        "question_text": {"type": "string", "description": "Target question text (optional)"},
        "competency_targeted": {"type": "string", "description": "Target competency (optional)"},
        "difficulty": {"type": "string", "description": "Target difficulty (optional)"},
    },
    handler=score_answer_rubric,
    required_params=[],
)

mcp_server.register_tool(
    name="persist_agent_output",
    description="Write a structured agent execution log entry to the database",
    parameters={
        "db_session": {"type": "object"},
        "interview_id": {"type": "string"},
        "agent_name": {"type": "string"},
        "node_status": {"type": "string"},
        "input_snapshot": {"type": "object"},
        "output_snapshot": {"type": "object"},
        "latency_ms": {"type": "integer"},
        "retry_count": {"type": "integer"},
        "prompt_version": {"type": "string"},
    },
    handler=persist_agent_output,
    required_params=["db_session", "interview_id", "agent_name", "node_status",
                     "input_snapshot", "output_snapshot"],
)

mcp_server.register_tool(
    name="generate_report_pdf",
    description="Generate a downloadable PDF/text report from structured interview report data",
    parameters={
        "report_data": {"type": "object", "description": "Full structured interview report"},
        "output_dir": {"type": "string", "description": "Directory to write PDF to"},
    },
    handler=generate_report_pdf,
    required_params=["report_data"],
)

# ── Register all v1 resources ────────────────────────────────

mcp_server.register_resource(
    uri_template="resource://industry-standards/{role}",
    description="Industry competency benchmarks for a role",
    handler=industry_standards_handler,
)
mcp_server.register_resource(
    uri_template="resource://competency-templates/{role}",
    description="Default competency weighting template for a role",
    handler=competency_templates_handler,
)
mcp_server.register_resource(
    uri_template="resource://question-bank/{role}/{difficulty}",
    description="Fallback seed question bank by role and difficulty",
    handler=question_bank_handler,
)

__all__ = ["mcp_server"]
