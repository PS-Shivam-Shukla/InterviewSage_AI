"""
Parallel Concurrency & State Thread Isolation Test (P1-6 / P2-5).
Verifies that simultaneous graph executions under different thread_ids execute concurrently
without state or observation cross-contamination.
"""

import asyncio
import pytest
from app.graph.graph_builder import build_graph


@pytest.mark.asyncio
async def test_parallel_thread_state_isolation():
    app = build_graph(allow_stubs=False)

    state_1 = {
        "interview_id": "interview_session_alpha",
        "pending_answer": "Interview Alpha answer using Python GIL knowledge.",
        "current_question": {"question_text": "What is GIL?", "sequence_number": 1},
    }
    config_1 = {"configurable": {"thread_id": "interview_session_alpha"}}

    state_2 = {
        "interview_id": "interview_session_beta",
        "pending_answer": "Interview Beta answer using PostgreSQL indexing.",
        "current_question": {"question_text": "How do indexes work?", "sequence_number": 1},
    }
    config_2 = {"configurable": {"thread_id": "interview_session_beta"}}

    # Execute both graph invocations concurrently
    task_1 = asyncio.to_thread(app.invoke, state_1, config_1)
    task_2 = asyncio.to_thread(app.invoke, state_2, config_2)

    res_1, res_2 = await asyncio.gather(task_1, task_2)

    assert res_1.get("interview_id") == "interview_session_alpha"
    assert res_2.get("interview_id") == "interview_session_beta"
    assert res_1 != res_2
