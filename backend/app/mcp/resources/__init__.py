"""MCP resource handlers."""

from app.mcp.tools.fetch_industry_standards import fetch_industry_standards


def industry_standards_handler(role: str):
    return fetch_industry_standards(role)


def competency_templates_handler(role: str):
    """Return a default competency template for the role."""
    standards = fetch_industry_standards(role)
    return {"competencies": standards.get("key_competencies", [])}


def question_bank_handler(role: str, difficulty: str):
    """
    Fallback question bank — used only when the Question Generator
    fails all retries.  Returns a small set of generic seed questions.
    """
    return {
        "questions": [
            {
                "text": f"Can you walk me through your experience with {role}?",
                "competency_targeted": "Communication",
                "difficulty": difficulty,
                "round_type": "HR",
            },
            {
                "text": "Describe a challenging technical problem you solved recently.",
                "competency_targeted": "Problem Solving",
                "difficulty": difficulty,
                "round_type": "TECHNICAL",
            },
            {
                "text": "How do you approach learning new technologies?",
                "competency_targeted": "Growth Mindset",
                "difficulty": "EASY",
                "round_type": "HR",
            },
        ]
    }
