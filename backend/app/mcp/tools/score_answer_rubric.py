"""
MCP Tool: score_answer_rubric
Selects and returns the correct rubric template for a given
question type, or evaluates an answer dynamically against the rubric when answer_text is provided.
"""

from typing import Any, Literal

QuestionType = Literal["behavioral", "fundamentals", "advanced", "system_design", "aptitude"]


# ── Rubric templates ──────────────────────────────────────────────────────────

_RUBRICS: dict[str, dict[str, Any]] = {
    "aptitude": {
        "dimensions": [
            {
                "name": "Correctness & Accuracy",
                "weight": 40,
                "description": "Mathematical, quantitative, or logical accuracy of the final solution",
                "anchors": {
                    1: "Factually or mathematically incorrect solution",
                    3: "Partially correct approach with minor calculation error",
                    5: "Flawlessly correct mathematical solution",
                },
            },
            {
                "name": "Reasoning & Approach",
                "weight": 40,
                "description": "Step-by-step logical derivation, calculation methodology, or analytical approach",
                "anchors": {
                    1: "No logical approach or random guessing",
                    3: "Sound method with minor derivation gaps",
                    5: "Clear, structured, and mathematically sound derivation",
                },
            },
            {
                "name": "Clarity & Structure",
                "weight": 20,
                "description": "Clear presentation of the quantitative answer and reasoning",
                "anchors": {
                    1: "Unclear or ambiguous final statement",
                    3: "Understandable numerical response",
                    5: "Crisp, concise, and structured presentation",
                },
            },
        ],
        "scoring_range": (1, 100),
        "method": "weighted_average",
    },
    "behavioral": {
        "dimensions": [
            {
                "name": "Situation Clarity",
                "weight": 20,
                "description": "How clearly the candidate described the context and challenge",
                "anchors": {
                    1: "No context given, vague generalities",
                    3: "Basic context provided",
                    5: "Crisp, specific situation with measurable stakes",
                },
            },
            {
                "name": "Task & Ownership",
                "weight": 20,
                "description": "Whether the candidate clearly owned the task",
                "anchors": {
                    1: "Unclear what the candidate's role was",
                    3: "Candidate's responsibility loosely described",
                    5: "Crystal-clear personal ownership and accountability",
                },
            },
            {
                "name": "Action Quality",
                "weight": 30,
                "description": "Specific actions taken and rationale behind decisions",
                "anchors": {
                    1: "Passive, group-focused, no individual action shown",
                    3: "Actions described but lack depth or rationale",
                    5: "Proactive, strategic, well-justified personal actions",
                },
            },
            {
                "name": "Result & Impact",
                "weight": 15,
                "description": "Measurable outcome and lessons learned",
                "anchors": {
                    1: "No result mentioned or negative outcome unaddressed",
                    3: "Qualitative result given",
                    5: "Quantified metric-driven result with explicit reflection",
                },
            },
            {
                "name": "Confidence",
                "weight": 15,
                "description": "Assertiveness, conviction, and lack of excessive hedging",
                "anchors": {
                    1: "Excessive hedging, uncertainty, self-doubt",
                    3: "Moderate confidence with minor hedging",
                    5: "Clear conviction, decisive ownership, and assertive explanation",
                },
            },
        ],
        "scoring_range": (1, 100),
        "method": "weighted_average",
    },
    "fundamentals": {
        "dimensions": [
            {
                "name": "Correctness",
                "weight": 35,
                "description": "Technical accuracy of core concepts",
                "anchors": {
                    1: "Factually incorrect or major misconceptions",
                    3: "Partially correct with minor inaccuracies",
                    5: "Flawlessly correct with precise technical terminology",
                },
            },
            {
                "name": "Completeness",
                "weight": 25,
                "description": "Coverage of essential components of the question",
                "anchors": {
                    1: "Missed core aspects of the topic",
                    3: "Covered primary cases, missed key nuances",
                    5: "Comprehensive coverage including edge cases",
                },
            },
            {
                "name": "Communication",
                "weight": 20,
                "description": "Logically structured, clear, and coherent explanation",
                "anchors": {
                    1: "Confusing or disjointed explanation",
                    3: "Understandable with effort",
                    5: "Structured, concise, and easy to follow",
                },
            },
            {
                "name": "Confidence",
                "weight": 20,
                "description": "Assertiveness and absence of excessive hedging phrases",
                "anchors": {
                    1: "Excessive hedging ('maybe', 'I think', 'I guess')",
                    3: "Reasonably confident with minor hesitation",
                    5: "Assertive, well-reasoned, and confident technical delivery",
                },
            },
        ],
        "scoring_range": (1, 100),
        "method": "weighted_average",
    },
    "advanced": {
        "dimensions": [
            {
                "name": "Deep Technical Depth",
                "weight": 30,
                "description": "Understanding of underlying mechanics, memory, protocols, or internals",
                "anchors": {
                    1: "Surface-level knowledge only",
                    3: "Good high-level understanding, gaps in internals",
                    5: "Mastery of internal mechanics and implementation details",
                },
            },
            {
                "name": "Trade-off Analysis",
                "weight": 25,
                "description": "Ability to evaluate technical trade-offs and alternatives",
                "anchors": {
                    1: "Sees solutions as binary, ignores trade-offs",
                    3: "Mentions trade-offs when prompted",
                    5: "Proactively evaluates space/time/complexity trade-offs",
                },
            },
            {
                "name": "Edge Cases & Safety",
                "weight": 20,
                "description": "Anticipating failure modes, race conditions, memory leaks",
                "anchors": {
                    1: "Ignores failure modes",
                    3: "Identifies obvious failure scenarios",
                    5: "Robustly addresses concurrency, failures, and edge cases",
                },
            },
            {
                "name": "Communication",
                "weight": 15,
                "description": "Clarity of advanced technical walkthrough",
                "anchors": {
                    1: "Disorganized or unclear technical narrative",
                    3: "Clear explanation of technical design",
                    5: "Exceptionally articulate, precise, and well-structured",
                },
            },
            {
                "name": "Confidence",
                "weight": 10,
                "description": "Conviction in technical decisions and trade-offs",
                "anchors": {
                    1: "Uncertain, heavy hedging on design choices",
                    3: "Solid confidence with minor hesitation",
                    5: "Strong technical conviction backed by empirical reasoning",
                },
            },
        ],
        "scoring_range": (1, 100),
        "method": "weighted_average",
    },
    "system_design": {
        "dimensions": [
            {
                "name": "Requirements & Scope",
                "weight": 15,
                "description": "Clarifying functional and non-functional requirements",
                "anchors": {
                    1: "Jumped straight to solution without scoping",
                    3: "Asked basic clarifying questions",
                    5: "Drove structured requirement gathering and scale estimates",
                },
            },
            {
                "name": "Architecture & Components",
                "weight": 30,
                "description": "Clean separation of components, APIs, and data flows",
                "anchors": {
                    1: "Monolithic, unscalable proposal",
                    3: "Standard architecture with minor gaps",
                    5: "Highly scalable, decoupled, production-ready architecture",
                },
            },
            {
                "name": "Scalability & Reliability",
                "weight": 20,
                "description": "Handling scale, bottlenecks, caching, partitioning, fault tolerance",
                "anchors": {
                    1: "Fails under scale, single points of failure",
                    3: "Addresses scaling basics (load balancers, caching)",
                    5: "Deep strategy for sharding, replication, failover, rate-limiting",
                },
            },
            {
                "name": "Data Storage & Model",
                "weight": 15,
                "description": "Appropriate DB selection and schema design",
                "anchors": {
                    1: "No data design",
                    3: "Basic schema described",
                    5: "Thoughtful schema with indexing, partitioning, and query patterns",
                },
            },
            {
                "name": "Communication",
                "weight": 10,
                "description": "Clarity of the walkthrough",
                "anchors": {
                    1: "Disorganised",
                    3: "Followable",
                    5: "Exceptionally structured and clear",
                },
            },
            {
                "name": "Confidence",
                "weight": 10,
                "description": "Assertiveness and conviction in system trade-offs",
                "anchors": {
                    1: "Hesitant or uncertain architectural recommendations",
                    3: "Solid architectural confidence",
                    5: "Decisive system architecture defense with clear trade-offs",
                },
            },
        ],
        "scoring_range": (1, 100),
        "method": "weighted_average",
    },
}


def score_answer_rubric(
    question_type: str = "fundamentals",
    seniority_level: str = "MID",
    answer_text: str | None = None,
    question_text: str | None = None,
    competency_targeted: str | None = None,
    difficulty: str | None = None,
) -> dict[str, Any]:
    """
    Return the scoring rubric for a given question type and seniority level.
    If answer_text is provided, dynamically evaluates the answer using the authoritative EvaluationAgent.
    """
    if answer_text is not None:
        from app.agents.evaluation_agent import EvaluationAgent
        # Construct the state payload expected by EvaluationAgent
        state = {
            "current_question": {
                "question_text": question_text or "What is Python GIL?",
                "competency_targeted": competency_targeted or "General",
                "question_type": question_type or "fundamentals",
                "difficulty": difficulty or "MEDIUM",
            },
            "answers": [{"answer_text": answer_text}],
            "profile_summary": {"calibrated_seniority": seniority_level or "MID"},
        }
        agent = EvaluationAgent()
        res = agent._run(state)
        # Return the evaluated record dict
        return res.get("evaluations", [{}])[0]

    normalised = (question_type or "fundamentals").lower().replace(" ", "_").replace("-", "_")

    aliases = {
        "behavioural": "behavioral",
        "hr": "behavioral",
        "culture": "behavioral",
        "fundamental": "fundamentals",
        "basic": "fundamentals",
        "core": "fundamentals",
        "design": "system_design",
        "architecture": "system_design",
        "aptitude": "fundamentals",
    }
    normalised = aliases.get(normalised, normalised)

    rubric = _RUBRICS.get(normalised, _RUBRICS["fundamentals"]).copy()

    rubric["seniority_context"] = {
        "JUNIOR": "Apply lenient thresholds; reward clear fundamentals even if incomplete",
        "MID": "Apply standard thresholds; expect solid fundamentals and reasonable depth",
        "SENIOR": "Apply strict thresholds; expect depth, tradeoffs, and nuanced edge-case handling",
    }.get((seniority_level or "MID").upper(), "Apply standard thresholds")

    return rubric
