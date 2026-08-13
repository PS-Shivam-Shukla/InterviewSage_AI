# Phase 3 — Sprint 6: Durable LangGraph State Architecture Discovery Report

**Role**: Principal AI Architect, Staff Backend Engineer, & Senior LangGraph Engineer  
**Scope**: Discovery and Architectural Blueprint for Durable Multi-Turn LangGraph State Persistence using PostgreSQL Checkpointing (`PostgresSaver`).  
**Constraint Verification**: Discovery & Analysis phase. Zero application business logic or prompt changes.

---

## 1. Current LangGraph Lifecycle & Audit Findings

### 1.1 Existing Graph Topology & Construction (`app/graph/workflow_master.py`)

The current master workflow graph is built using LangGraph's `StateGraph` with state schema `InterviewState` (`TypedDict`):

```python
graph = StateGraph(InterviewState)

graph.add_node("classify_candidate", classify_candidate_node)
graph.add_node("generate_blueprint", generate_blueprint_node)
graph.add_node("personalize_question", personalize_question_node)
graph.add_node("evaluate_answer", evaluate_answer_node)

graph.set_entry_point("classify_candidate")

graph.add_edge("classify_candidate", "generate_blueprint")
graph.add_edge("generate_blueprint", "personalize_question")
graph.add_edge("personalize_question", "evaluate_answer")

graph.add_conditional_edges(
    "evaluate_answer",
    route_next_step,
    {
        "personalize_question": "personalize_question",
        "end": END,
    },
)
return graph.compile()
```

### 1.2 Identified Weaknesses in Current Execution Model

1. **Request-Scoped Execution**:
   - `build_master_workflow()` compiles the graph **without a checkpointer** (`checkpointer=None`).
   - Every execution is un-checkpointed:
     ```python
     # Current call site in interview_service.py:
     graph_output = master_workflow.invoke(initial_state)
     ```
2. **Ephemeral Thread Identity**:
   - `invoke()` is currently called without a `config={"configurable": {"thread_id": interview_id}}`.
   - Node outputs are evaluated in memory for a single call and forgotten immediately after the request completes.
3. **No Resumption Across Turns**:
   - When a candidate submits an answer on Turn 2 or Turn 3, the graph does NOT resume from its previous step (`evaluate_answer` -> `personalize_question`). Instead, state was previously synthesized via process-local dictionaries.
4. **Vulnerability to Restart / Horizontal Scaling**:
   - Server restarts, Gunicorn worker recycles, or Kubernetes pod failovers wipe out transient state because the graph progress is never checkpointed to PostgreSQL.

---

## 2. Target Durable Checkpointing Architecture

```
                                [ HTTP Client Request ]
                                           │
                                           ▼
                            FastAPI Route / InterviewService
                                           │
                            Thread Identity Config:
                    config = {"configurable": {"thread_id": interview.id}}
                                           │
                                           ▼
                                 LangGraph Master Workflow
                                  (Compiled with Checkpointer)
                                           │
                            ┌──────────────┴──────────────┐
                            ▼                             ▼
                    [ Execute Graph Node ]       [ Read/Write Checkpoint ]
                            │                             │
                            │                             ▼
                            │                      PostgreSQL Database
                            │                     (checkpoints & writes)
                            ▼
                    [ Updated Graph State ]
```

---

## 3. Required Architectural Changes

1. **Checkpointer Initialization (`app/graph/workflow_master.py` & `app/core/database.py`)**:
   - Integrate `PostgresSaver` (or standard `MemorySaver` fallback when running SQLite memory unit tests) into `graph.compile(checkpointer=checkpointer)`.
   - Use `PostgresSaver` connected to the application's primary database pool.
2. **Permanent Thread ID Configuration (`app/services/interview_service.py`)**:
   - Every call to `get_interview_plan()`, `submit_answer()`, or turn progression MUST pass:
     ```python
     config = {"configurable": {"thread_id": interview_id}}
     graph_output = master_workflow.invoke(state, config=config)
     ```
   - `interview_id` is the permanent, deterministic identity for the graph execution thread.
3. **State Resumption Logic**:
   - When `invoke(state, config=config)` is called for an existing `thread_id`, LangGraph automatically loads the latest checkpoint from PostgreSQL and executes only the pending steps, avoiding duplicate execution of completed nodes (`classify_candidate`, `generate_blueprint`).

---

## 4. Risk Analysis & Mitigation Strategies

| Potential Risk | Severity | Root Cause | Mitigation Strategy |
|---|:---:|---|---|
| **Database Pool Exhaustion** | Medium | Opening separate connection pools inside `PostgresSaver` | Use connection strings from `settings.database_url` with pooled connection management or shared connection context. |
| **SQLite Unit Test Incompatibility** | Medium | `PostgresSaver` requires PostgreSQL syntax (`psycopg`) | Implement a factory function `get_checkpointer()` that uses `PostgresSaver` for PostgreSQL URLs and `MemorySaver` / SQLite checkpointer for in-memory SQLite unit tests. |
| **Checkpoint State Schema Evolution** | Low | Modifying `GraphState` TypedDict keys over time | Preserve backward-compatible default keys (`resume_json`, `jd_json`, `classification`, `evaluations`) in `GraphState`. |
| **Concurrent Request Race Conditions** | Low | Two requests for the same `thread_id` arriving simultaneously | LangGraph thread locking combined with PostgreSQL row-level locks prevents concurrent state corruption. |

---

## 5. Migration Strategy

1. **Phase 1 — Checkpointer Factory**:
   - Add `get_checkpointer(database_url: str | None = None)` in `app/graph/workflow_master.py` (or `app/core/database.py`).
2. **Phase 2 — Graph Compilation with Checkpointer**:
   - Update `build_master_workflow(checkpointer=None)` to accept an optional checkpointer instance.
3. **Phase 3 — Service Integration**:
   - Update `InterviewService` methods (`get_interview_plan`, `submit_answer`) to pass `config={"configurable": {"thread_id": interview_id}}` on every invoke.
4. **Phase 4 — Durable Recovery & Testing**:
   - Add unit, integration, recovery, and regression tests in `app/tests/test_langgraph_checkpointing.py`.
