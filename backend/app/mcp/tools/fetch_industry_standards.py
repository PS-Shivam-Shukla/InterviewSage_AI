"""
MCP Tool / Resource handler: fetch_industry_standards
Returns role-specific competency benchmarks and common skill expectations.
In v1 this is a curated static dictionary; it will later connect to a
live external knowledge source.
"""

from typing import Any

# ── Static knowledge base ─────────────────────────────────────────────────────
# Each entry represents expected skills / competencies for a role category.
# Keyed by normalised role slug.

_STANDARDS: dict[str, dict[str, Any]] = {
    "backend-engineer": {
        "core_skills": ["Python", "REST APIs", "SQL", "Data Modelling", "Testing", "Git"],
        "advanced_skills": ["System Design", "Distributed Systems", "Caching", "Message Queues"],
        "industry_tools": ["FastAPI", "Django", "PostgreSQL", "Redis", "Docker"],
        "seniority_expectations": {
            "JUNIOR": "Solid fundamentals, able to build features under guidance",
            "MID": "Owns features end-to-end, familiar with system design basics",
            "SENIOR": "Leads design decisions, mentors team, deep expertise in ≥1 sub-domain",
        },
        "key_competencies": [
            {"name": "Coding", "weight": 30},
            {"name": "System Design", "weight": 25},
            {"name": "Debugging", "weight": 15},
            {"name": "Communication", "weight": 15},
            {"name": "Culture Fit", "weight": 15},
        ],
    },
    "frontend-engineer": {
        "core_skills": ["JavaScript", "TypeScript", "React", "CSS", "HTML", "Git"],
        "advanced_skills": ["Performance Optimisation", "Accessibility", "State Management", "SSR"],
        "industry_tools": ["React", "Next.js", "Vite", "TailwindCSS", "Webpack"],
        "seniority_expectations": {
            "JUNIOR": "Builds UI components, understands browser fundamentals",
            "MID": "Designs component architecture, handles state complexity",
            "SENIOR": "Leads frontend architecture, owns performance and DX",
        },
        "key_competencies": [
            {"name": "JavaScript/TypeScript", "weight": 30},
            {"name": "UI/UX Thinking", "weight": 25},
            {"name": "Performance", "weight": 20},
            {"name": "Communication", "weight": 15},
            {"name": "Culture Fit", "weight": 10},
        ],
    },
    "fullstack-engineer": {
        "core_skills": ["JavaScript", "TypeScript", "Python", "React", "REST APIs", "SQL"],
        "advanced_skills": ["System Design", "DevOps basics", "Cloud fundamentals"],
        "industry_tools": ["React", "Node.js", "FastAPI", "PostgreSQL", "Docker"],
        "seniority_expectations": {
            "JUNIOR": "Can contribute to both frontend and backend under guidance",
            "MID": "Delivers features across the stack independently",
            "SENIOR": "Architects full solutions, makes technology trade-off decisions",
        },
        "key_competencies": [
            {"name": "Coding", "weight": 35},
            {"name": "System Design", "weight": 25},
            {"name": "Communication", "weight": 20},
            {"name": "Culture Fit", "weight": 20},
        ],
    },
    "data-engineer": {
        "core_skills": ["Python", "SQL", "ETL Pipelines", "Data Warehousing", "Spark"],
        "advanced_skills": ["Streaming (Kafka)", "Data Modelling", "Orchestration (Airflow)"],
        "industry_tools": ["Apache Spark", "dbt", "Airflow", "Snowflake", "BigQuery"],
        "seniority_expectations": {
            "JUNIOR": "Writes and maintains ETL jobs",
            "MID": "Designs pipelines, owns data quality",
            "SENIOR": "Architects data platform, drives data strategy",
        },
        "key_competencies": [
            {"name": "Data Engineering", "weight": 35},
            {"name": "SQL & Querying", "weight": 25},
            {"name": "System Design", "weight": 20},
            {"name": "Communication", "weight": 20},
        ],
    },
    "ml-engineer": {
        "core_skills": ["Python", "PyTorch/TensorFlow", "Scikit-learn", "SQL", "Statistics"],
        "advanced_skills": ["MLOps", "Feature Engineering", "Model Serving", "Distributed Training"],
        "industry_tools": ["PyTorch", "Scikit-learn", "MLflow", "Docker", "Kubernetes"],
        "seniority_expectations": {
            "JUNIOR": "Implements models from research papers, familiar with ML lifecycle",
            "MID": "End-to-end model development and deployment",
            "SENIOR": "Designs ML systems, leads research direction",
        },
        "key_competencies": [
            {"name": "ML Fundamentals", "weight": 35},
            {"name": "System Design", "weight": 20},
            {"name": "Coding", "weight": 25},
            {"name": "Communication", "weight": 20},
        ],
    },
    "default": {
        "core_skills": ["Communication", "Problem Solving", "Teamwork", "Adaptability"],
        "advanced_skills": ["Leadership", "Strategic Thinking", "Domain Expertise"],
        "industry_tools": [],
        "seniority_expectations": {
            "JUNIOR": "Learning role fundamentals, needs guidance",
            "MID": "Independent contributor with proven track record",
            "SENIOR": "Expert and leader in their domain",
        },
        "key_competencies": [
            {"name": "Technical Skills", "weight": 40},
            {"name": "Communication", "weight": 30},
            {"name": "Problem Solving", "weight": 30},
        ],
    },
}


def fetch_industry_standards(role: str) -> dict[str, Any]:
    """
    Return industry standards for a given role.

    Args:
        role: Role slug, e.g. "backend-engineer", "frontend-engineer".
              Will be normalised (lowercased, spaces → hyphens).

    Returns:
        Industry standards dict with core_skills, advanced_skills,
        industry_tools, seniority_expectations, key_competencies.
    """
    normalised = role.lower().replace(" ", "-").replace("_", "-")

    # Try exact match first, then prefix match, then default
    if normalised in _STANDARDS:
        return _STANDARDS[normalised]

    for key in _STANDARDS:
        if key != "default" and (normalised.startswith(key) or key.startswith(normalised)):
            return _STANDARDS[key]

    return _STANDARDS["default"]
