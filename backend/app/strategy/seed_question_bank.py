"""
Seed Question Bank (Phase 6).
Provides deterministic, high-quality fallback and startup questions
grouped by round type, competency, difficulty, and cognitive angle.
"""

import re
from typing import Any

# Default competencies when target competency is not specified
DEFAULT_COMPETENCIES = {
    "TECHNICAL": "Software Engineering",
    "HR": "Communication & Collaboration",
    "APTITUDE": "Quantitative Reasoning",
}

# Calibrated, highly domain-aligned seed question dictionary
SEED_QUESTIONS_DB: dict[str, dict[str, dict[str, dict[str, str]]]] = {
    "TECHNICAL": {
        "react": {
            "EASY": {
                "fundamentals_and_concepts": "What is the Virtual DOM in React, and how does React use it to optimize rendering performance?",
                "implementation_and_usage": "Explain the difference between functional components with hooks and class components in React.",
                "default": "What is the purpose of React hooks, and how do useState and useEffect manage state and side effects?",
            },
            "MEDIUM": {
                "fundamentals_and_concepts": "Explain how React's reconciliation algorithm works and why the 'key' prop is essential for list rendering.",
                "implementation_and_usage": "How do you implement a custom Hook in React to share stateful logic between components?",
                "debugging_and_failure_investigation": "How would you diagnose and resolve an infinite re-render loop caused by useEffect dependency arrays?",
                "architecture_and_design_tradeoffs": "Compare Context API and Redux for global state management in React. In what scenarios would you choose Redux?",
                "performance_and_optimization": "Explain how React.memo, useMemo, and useCallback can be used to prevent unnecessary component re-renders.",
                "default": "How do you optimize render performance and structure component lifecycle hooks in a React application?",
            },
            "HARD": {
                "architecture_and_design_tradeoffs": "Design a state management and component structure for a multi-step form wizard in React. How would you persist data and handle validation?",
                "performance_and_optimization": "Explain React Fiber architecture, concurrent rendering features, and how transitions (useTransition) improve UI responsiveness.",
                "default": "Explain React's hydration process in Server-Side Rendering (SSR) and how you would optimize Cumulative Layout Shift (CLS) on the frontend.",
            },
        },
        "python": {
            "EASY": {
                "fundamentals_and_concepts": "Explain the difference between list and tuple in Python, and when you would choose one over the other.",
                "implementation_and_usage": "How do you read a text file safely in Python ensuring the file is closed even if an exception occurs?",
                "default": "Explain standard decorators in Python like @staticmethod, @classmethod, and @property.",
            },
            "MEDIUM": {
                "fundamentals_and_concepts": "Explain how Python manages memory, references, and how garbage collection handles circular references.",
                "implementation_and_usage": "How do you implement a custom context manager in Python using both class-based methods and the contextlib library?",
                "debugging_and_failure_investigation": "How do you identify and diagnose a memory leak in a running Python application using standard tools?",
                "architecture_and_design_tradeoffs": "Explain the Global Interpreter Lock (GIL) in Python and its impact on multi-threading vs multi-processing vs asyncio.",
                "performance_and_optimization": "Compare list comprehensions, generators, and map() in Python. When would you use a generator to optimize memory?",
                "default": "Explain how exception propagation works in Python and how to implement custom exception classes.",
            },
            "HARD": {
                "architecture_and_design_tradeoffs": "Explain how Python metaclasses work and how you would use them to enforce validation constraints on subclass attributes during import time.",
                "performance_and_optimization": "How would you optimize a CPU-bound Python script using Cython, multiprocessing, or JIT compilers like PyPy?",
                "default": "Explain the mechanics of descriptor protocols in Python and how they underly the implementation of @property and methods.",
            },
        },
        "postgresql": {
            "EASY": {
                "fundamentals_and_concepts": "Explain the difference between a primary key and a foreign key constraint in relational databases.",
                "implementation_and_usage": "Write a SQL query that retrieves duplicate email records from a users table.",
                "default": "What is database normalization, and explain the difference between 1NF, 2NF, and 3NF.",
            },
            "MEDIUM": {
                "fundamentals_and_concepts": "Explain Multi-Version Concurrency Control (MVCC) in PostgreSQL and how it enables non-blocking concurrent reads and writes.",
                "implementation_and_usage": "Explain index-only scans in PostgreSQL and how to write queries that benefit from them.",
                "debugging_and_failure_investigation": "How do you analyze slow queries using EXPLAIN ANALYZE? What indicators tell you an index is missing?",
                "architecture_and_design_tradeoffs": "Compare transaction isolation levels in PostgreSQL. What concurrency anomalies does Serializable isolation prevent?",
                "performance_and_optimization": "How do database indexes improve query latency in PostgreSQL? Compare B-Tree, Hash, and GIN indexes.",
                "default": "Explain the difference between database clustering, replication (logical vs physical), and partitioning in PostgreSQL.",
            },
            "HARD": {
                "performance_and_optimization": "How do you optimize write performance in PostgreSQL for high-throughput ingestion? Discuss WAL configuration, autovacuum parameters, and bulk loading.",
                "architecture_and_design_tradeoffs": "Design a high-availability PostgreSQL cluster configuration with connection poolers. Compare pgBouncer, Pgpool-II, and application-side pooling.",
                "default": "Explain index write amplification (HOT updates) in PostgreSQL and how fillfactor adjustments mitigate page splits.",
            },
        },
        "system design": {
            "MEDIUM": {
                "fundamentals_and_concepts": "Explain the CAP theorem and the trade-offs between consistency and availability in a distributed database system.",
                "implementation_and_usage": "How would you implement a distributed rate limiter for API endpoints serving 50k requests per second?",
                "debugging_and_failure_investigation": "How do you investigate and handle a sudden cache stampede or thundering herd problem in a production cache tier?",
                "architecture_and_design_tradeoffs": "Compare microservices and monolithic architectures. What are the operational, latency, and deployment trade-offs?",
                "performance_and_optimization": "How do you handle horizontal scaling, connection pooling, and caching to support 100k requests per second?",
                "default": "Explain the role of message queues (e.g. RabbitMQ vs Kafka) in decoupling microservices architectures.",
            },
            "HARD": {
                "architecture_and_design_tradeoffs": "Design a global real-time notification system supporting 100M active connections. Discuss WebSocket management, pub/sub brokers, and geo-routing.",
                "performance_and_optimization": "Design a highly available distributed session cache that handles millions of writes per second with consistency guarantees. How do you resolve partition splits?",
                "default": "Explain consensus algorithms like Raft or Paxos, and how distributed coordination services (e.g., ZooKeeper, Consul) maintain cluster states.",
            },
        },
    },
    "HR": {
        "communication": {
            "EASY": {
                "default": "Tell me about yourself and your background. What motivates you as a developer?",
            },
            "MEDIUM": {
                "default": "Describe a situation where you had to explain a complex technical concept to a non-technical stakeholder. How did you ensure clarity?",
            },
        },
        "collaboration": {
            "EASY": {
                "default": "How do you handle feedback on your code during peer review? Can you share a positive experience?",
            },
            "MEDIUM": {
                "default": "Tell me about a time you had a conflict with a teammate on a project deadline. How did you collaborate to resolve it?",
            },
        },
        "adaptability": {
            "MEDIUM": {
                "default": "Can you describe a situation where you had to adapt to changing project requirements or tight deadlines under pressure?",
            },
        },
    },
    "APTITUDE": {
        "quantitative reasoning": {
            "EASY": {
                "default": "If task A takes 4 hours and task B takes 6 hours, how long would they take working together at constant rates?",
            },
            "MEDIUM": {
                "default": "If a system's throughput increases by 40% and latency decreases by 30%, what is the net relative efficiency improvement?",
            },
        },
        "logical reasoning": {
            "EASY": {
                "default": "Complete the logical pattern: A1, C3, E5, G7, ... What is the next element in the sequence?",
            },
            "MEDIUM": {
                "default": "In a distributed system, Node A is faster than B, B is slower than C, and C is faster than A. Which node is the slowest?",
            },
        },
    },
}


def _normalize_key(text: str) -> str:
    """Normalize skill name or competency string to match keys in SEED_QUESTIONS_DB."""
    cleaned = text.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s-]", "", cleaned)
    # Simplify framework names to base key
    if "react" in cleaned:
        return "react"
    if "python" in cleaned:
        return "python"
    if "postgre" in cleaned or "sql" in cleaned or "db" in cleaned:
        return "postgresql"
    if "system design" in cleaned or "architecture" in cleaned or "scaling" in cleaned:
        return "system design"
    if "communication" in cleaned or "team" in cleaned or "share" in cleaned or "write" in cleaned:
        return "communication"
    if "collaboration" in cleaned or "conflict" in cleaned or "people" in cleaned:
        return "collaboration"
    if "adapt" in cleaned or "change" in cleaned:
        return "adaptability"
    if "quant" in cleaned or "math" in cleaned or "number" in cleaned:
        return "quantitative reasoning"
    if "logic" in cleaned or "reason" in cleaned:
        return "logical reasoning"
    return cleaned


def get_seed_question(
    round_type: str,
    competency: str,
    difficulty: str,
    cognitive_angle: str | None = None,
    asked_questions: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Selects a deterministic seed-bank question matching round_type, competency,
    difficulty, and optional cognitive_angle, avoiding duplicates.
    """
    round_type_upper = (round_type or "TECHNICAL").upper()
    comp_norm = _normalize_key(competency or DEFAULT_COMPETENCIES.get(round_type_upper, "General"))
    diff_norm = (difficulty or "MEDIUM").upper()
    if diff_norm not in ["EASY", "MEDIUM", "HARD", "ADVANCED"]:
        diff_norm = "MEDIUM"

    asked_texts = {q.get("question_text", "").strip().lower() for q in (asked_questions or []) if isinstance(q, dict)}

    # Step 1: Lookup in the custom calibrated DB
    round_db = SEED_QUESTIONS_DB.get(round_type_upper, SEED_QUESTIONS_DB["TECHNICAL"])
    comp_db = round_db.get(comp_norm)

    # If competency not found, fallback to first available key in the round
    if not comp_db:
        comp_db = list(round_db.values())[0] if round_db else {}

    # Find matching difficulty level
    diff_db = comp_db.get(diff_norm)
    if not diff_db:
        # Try MEDIUM as default, otherwise take first difficulty available
        diff_db = comp_db.get("MEDIUM") or (list(comp_db.values())[0] if comp_db else {})

    # Try requested cognitive_angle first, then default, then first available
    q_text = None
    if cognitive_angle and diff_db.get(cognitive_angle):
        candidate_text = diff_db[cognitive_angle]
        if candidate_text.strip().lower() not in asked_texts:
            q_text = candidate_text

    if not q_text and diff_db.get("default"):
        candidate_text = diff_db["default"]
        if candidate_text.strip().lower() not in asked_texts:
            q_text = candidate_text

    # Take any question in this difficulty subset not asked
    if not q_text:
        for txt in diff_db.values():
            if txt.strip().lower() not in asked_texts:
                q_text = txt
                break

    # Step 2: If still none or already asked, construct a generic competency-aligned seed question dynamically
    if not q_text:
        if round_type_upper == "HR":
            q_text = f"Can you describe a situation in your previous projects where you demonstrated strong '{competency}' skills?"
            q_type = "behavioral"
        elif round_type_upper == "APTITUDE":
            q_text = f"Apply logical reasoning and analytical skills to solve a complex problem involving '{competency}'."
            q_type = "fundamentals"
        else:
            q_text = f"Explain the core architectural principles, standard implementation patterns, and common failure modes of '{competency}' in production systems."
            q_type = "fundamentals"
    else:
        # Determine question type
        q_type = "fundamentals"
        if round_type_upper == "HR":
            q_type = "behavioral"
        elif diff_norm in ["HARD", "ADVANCED"]:
            q_type = "system_design"

    return {
        "question_text": q_text,
        "competency_targeted": competency,
        "difficulty": diff_norm,
        "question_type": q_type,
        "round_type": round_type_upper,
        "cognitive_angle": cognitive_angle or "fundamentals_and_concepts",
        "fallback_used": True,
        "fallback_type": "seed_bank",
    }
