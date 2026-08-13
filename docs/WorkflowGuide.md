# Workflow Guide

## LangGraph State Machine

The interview workflow is modelled as a `StateGraph[InterviewState]` with 15 nodes. The graph is compiled once at startup via `build_graph()` in `backend/app/graph/graph_builder.py`.

### Resuming a paused interview

Every node completion writes a checkpoint keyed by `thread_id = interview_id`. To resume:

```python
from app.graph.graph_builder import build_graph

graph = build_graph(...)   # same real-agent instance
config = {"configurable": {"thread_id": interview_id}}

# Resume from last checkpoint — the graph figures out where it stopped
result = graph.invoke(None, config=config)
```

The `interview_service.py` handles this in `resume_interview()`.

### Debugging a stuck interview

1. Look up the `AGENT_LOG` rows for the interview:
   ```sql
   SELECT agent_name, node_status, latency_ms, retry_count, created_at
   FROM agent_logs
   WHERE interview_id = '<id>'
   ORDER BY created_at;
   ```
2. Find the last row with `node_status = 'FAILED'`.
3. Check `output_snapshot` for the error message.
4. The checkpoint holds the full `InterviewState` at failure point — inspect it via:
   ```python
   graph.get_state({"configurable": {"thread_id": interview_id}})
   ```

### Routing rules

| After node | Condition | Next node |
|---|---|---|
| `interview_planner_agent` | `hr_question_count > 0` | `question_generator_hr` |
| `interview_planner_agent` | `hr_question_count == 0` | `question_generator_tech` |
| `evaluation_agent_hr` | HR questions remaining | `question_generator_hr` |
| `evaluation_agent_hr` | HR round complete | `question_generator_tech` |
| `evaluation_agent_tech` | Tech questions remaining | `question_generator_tech` |
| `evaluation_agent_tech` | Tech round complete | `career_coach_agent` |

### Human-in-the-loop (answer submission)

The graph pauses at `hr_interview_agent` and `technical_interview_agent` waiting for `state["pending_answer"]`. The FastAPI `POST /interviews/{id}/answers` route sets this field and calls `graph.invoke(state_update, config=config)` to resume execution.

## Retry Logic

Every agent inherits from `BaseAgent` which wraps `_run()` with:
- Up to 2 retries on `ValidationError` or `ValueError`.
- On each retry, the validation error message is appended to the re-prompt.
- After 2 retries, `_on_failure()` is called (each agent has a specific safe fallback).

The `AGENT_LOG` records `retry_count` per execution — a sustained increase in retries for one agent is an early warning of prompt or schema drift.

## Prompt Versioning

Every `AGENT_LOG` row records `prompt_version`. To roll back a prompt regression:

1. Compare agent metrics for `prompt_version = v1` vs `v2` in the Admin Dashboard.
2. If `v2` shows higher retry rates or lower consistency scores, update the agent's `prompt_version = "v1"` and redeploy.
3. Investigate what changed in `v2` before promoting it again.
