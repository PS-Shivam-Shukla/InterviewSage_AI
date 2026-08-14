"""
MCP Tool: persist_agent_output
Writes a structured agent log entry to the database via the
AgentLogRepository. Every agent calls this after each node execution.
"""

import json
from typing import Any


def persist_agent_output(
    db_session: Any,
    interview_id: str,
    agent_name: str,
    node_status: str,
    input_snapshot: dict[str, Any],
    output_snapshot: dict[str, Any],
    latency_ms: int = 0,
    retry_count: int = 0,
    prompt_version: str | None = None,
) -> dict[str, Any]:
    """
    Persist one agent execution log entry.

    Args:
        db_session:       Active SQLAlchemy Session.
        interview_id:     ID of the owning interview.
        agent_name:       Name of the agent (e.g. "ResumeAgent").
        node_status:      "SUCCESS" | "RETRY" | "FAILED".
        input_snapshot:   Dict of key inputs (will be JSON-serialised).
        output_snapshot:  Dict of key outputs (will be JSON-serialised).
        latency_ms:       Wall-clock execution time in milliseconds.
        retry_count:      How many retries occurred before this result.
        prompt_version:   Prompt version string used (e.g. "v1").

    Returns:
        {"log_id": str, "status": "persisted"}
    """
    from app.models.interview import AgentLog

    log = AgentLog(
        interview_id=interview_id,
        agent_name=agent_name,
        node_status=node_status,
        input_snapshot=json.dumps(input_snapshot),
        output_snapshot=json.dumps(output_snapshot),
        latency_ms=latency_ms,
        retry_count=retry_count,
        prompt_version=prompt_version,
    )

    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)

    return {"log_id": log.id, "status": "persisted"}
