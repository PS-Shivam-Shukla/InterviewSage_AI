"""
LangGraph StateGraph builder (Section 8 of the master spec).

Assembles all 13 agent nodes + Supervisor into a typed state machine.
In Phase 5 every agent node is a STUB that passes state through; real
agent logic is layered in during Phases 6-9.

Graph topology:
    START
      └─> supervisor
            ├─> resume_agent
            │     └─> jd_agent
            │           └─> ats_agent
            │                 └─> profile_intelligence_agent
            │                       └─> competency_mapping_agent
            │                             └─> interview_planner_agent
            │                                   └─[conditional]─>
            │                                         ├─ question_generator_hr
            │                                         └─ question_generator_tech
            ├─> hr_interview_agent  ─> evaluation_agent_hr
            │         └─[loop / advance]─> question_generator_hr
            ├─> technical_interview_agent ─> evaluation_agent_tech
            │         └─[loop / advance]─> question_generator_tech
            ├─> career_coach_agent
            └─> report_generator_agent
                      └─> END
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.supervisor_agent import SupervisorAgent
from app.graph.state import InterviewState

_allow_stubs_global = True
_supervisor = SupervisorAgent()


def _compute_workflow_stage(state: InterviewState) -> str:
    stage = "INITIALIZING"
    if state.get("resume_data") or state.get("resume_json"):
        stage = "RESUME_ANALYSIS"
    if (state.get("resume_data") or state.get("resume_json")) and (state.get("jd_data") or state.get("jd_json")):
        stage = "JD_ANALYSIS"
    if state.get("interview_plan"):
        stage = "INTERVIEW_PLANNING"

    asked = state.get("questions_asked") or []
    answers = state.get("answers") or []
    evals = state.get("evaluations") or []

    if stage == "INTERVIEW_PLANNING" and asked:
        stage = "QUESTION_GENERATION"

    if stage == "QUESTION_GENERATION" and len(answers) < len(asked):
        stage = "WAITING_FOR_ANSWER"

    if stage == "QUESTION_GENERATION" and len(answers) == len(asked) and asked:
        if len(evals) == len(answers):
            stage = "ANSWER_EVALUATION"
        else:
            stage = "WAITING_FOR_ANSWER"

    if stage == "ANSWER_EVALUATION" and state.get("final_report"):
        stage = "REPORT_GENERATION"

    if state.get("final_report"):
        stage = "COMPLETED"
    return stage


def supervisor_node(state: InterviewState) -> dict:
    """Supervisor node handler — inspects state and updates next_node and workflow_stage."""
    stage = _compute_workflow_stage(state)
    temp_state = dict(state)
    temp_state["workflow_stage"] = stage
    next_node = _supervisor.decide_next_step(temp_state)
    return {
        "next_node": next_node,
        "workflow_stage": stage,
    }


def route_after_supervisor(state: InterviewState) -> str:
    """Entry & hub routing powered by SupervisorAgent decision engine."""
    stage = _compute_workflow_stage(state)
    temp_state = dict(state)
    temp_state["workflow_stage"] = stage
    return _supervisor.decide_next_step(temp_state)


def route_after_planner(state: InterviewState) -> str:
    """
    After the interview plan is built, decide which round starts first.
    Default: HR round first (if hr_question_count > 0).
    """
    plan = state.get("interview_plan") or {}
    if plan.get("hr_question_count", 0) > 0:
        return "question_generator_hr"
    return "question_generator_tech"


def route_after_hr_evaluation(state: InterviewState) -> str:
    """
    After each HR answer is evaluated, decide:
      - Ask another HR question, OR
      - Advance to technical round (if technical questions remain), OR
      - Move to post-interview (career coach).
    """
    plan = state.get("interview_plan") or {}
    hr_target = plan.get("hr_question_count", 5)
    tech_target = plan.get("technical_question_count", 7)

    hr_asked = sum(1 for q in (state.get("questions_asked") or []) if q.get("round_type") == "HR")
    tech_asked = sum(
        1 for q in (state.get("questions_asked") or []) if q.get("round_type") == "TECHNICAL"
    )

    if hr_asked < hr_target:
        return "question_generator_hr"
    if tech_asked < tech_target:
        return "question_generator_tech"
    return "career_coach_agent"


def route_after_tech_evaluation(state: InterviewState) -> str:
    """
    After each technical answer is evaluated, decide:
      - Ask another technical question, OR
      - Move to post-interview (career coach).
    """
    plan = state.get("interview_plan") or {}
    tech_target = plan.get("technical_question_count", 7)
    tech_asked = sum(
        1 for q in (state.get("questions_asked") or []) if q.get("round_type") == "TECHNICAL"
    )
    if tech_asked < tech_target:
        return "question_generator_tech"
    return "career_coach_agent"


def route_after_qgen_hr(state: InterviewState, allow_stubs: bool = True) -> str:
    """Route after HR question generation: pause if no pending answer is present."""
    if not state.get("pending_answer"):
        return END
    return "hr_interview_agent"


def route_after_qgen_tech(state: InterviewState, allow_stubs: bool = True) -> str:
    """Route after Technical question generation: pause if no pending answer is present."""
    if not state.get("pending_answer"):
        return END
    return "technical_interview_agent"


def _stub(name: str) -> Callable:
    def stub_handler(state: InterviewState) -> dict:
        return {"agent_log": [f"Stub node {name} executed"]}

    return stub_handler


def tool_executor_handler(state: InterviewState) -> dict:
    """ToolExecutor node handler — executes model-selected MCP tool and records observation."""
    decisions = state.get("policy_decisions") or []
    if not decisions:
        return {}

    latest_dec = decisions[-1]
    tool_name = latest_dec.get("tool")
    tool_args = latest_dec.get("arguments") or {}

    if not tool_name:
        return {"next_node": "policy_node"}

    from app.tools.executor import tool_executor

    obs = tool_executor.execute_tool(tool_name, tool_args)

    return {
        "observations": [obs.to_dict()],
        "next_node": "policy_node",
    }


def route_after_policy(state: InterviewState, allow_stubs: bool = False) -> str:
    """Dynamic router after PolicyNode decision."""
    nxt = state.get("next_node") or "report_generator_agent"
    if nxt == "report_generator_agent":
        if allow_stubs:
            return nxt
        plan = state.get("interview_plan") or {}
        target_count = plan.get("total_questions", 5)
        current_seq = state.get("current_question", {}).get("sequence_number") or len(state.get("questions_asked") or [])
        if current_seq < target_count:
            return END
    return nxt


# ─────────────────────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────────────────────


def build_graph(
    resume_agent: Callable = None,
    jd_agent: Callable = None,
    ats_agent: Callable = None,
    profile_intelligence_agent: Callable = None,
    competency_mapping_agent: Callable = None,
    interview_planner_agent: Callable = None,
    question_generator_hr: Callable = None,
    question_generator_tech: Callable = None,
    hr_interview_agent: Callable = None,
    technical_interview_agent: Callable = None,
    evaluation_agent_hr: Callable = None,
    evaluation_agent_tech: Callable = None,
    career_coach_agent: Callable = None,
    report_generator_agent: Callable = None,
    policy_node_handler: Callable = None,
    report_verification_handler: Callable = None,
    allow_stubs: bool = False,
    checkpointer: Any = None,
) -> StateGraph:
    """
    Build and compile the interview workflow StateGraph.

    When allow_stubs=False (Production Mode), missing agent callables default to concrete agent instances.
    When allow_stubs=True (Test/Stub Mode), missing agent callables default to pass-through stubs.
    """
    from app.agents import (
        ATSAgent,
        CareerCoachAgent,
        CompetencyMappingAgent,
        EvaluationAgent,
        HRInterviewAgent,
        InterviewPlannerAgent,
        JDAgent,
        ProfileIntelligenceAgent,
        QuestionGeneratorAgent,
        ReportGeneratorAgent,
        ResumeAgent,
        TechnicalInterviewAgent,
    )
    from app.graph.policy_node import policy_node
    from app.graph.report_verification_node import report_verification_node

    if not allow_stubs:
        resume_agent = resume_agent or ResumeAgent()
        jd_agent = jd_agent or JDAgent()
        ats_agent = ats_agent or ATSAgent()
        profile_intelligence_agent = profile_intelligence_agent or ProfileIntelligenceAgent()
        competency_mapping_agent = competency_mapping_agent or CompetencyMappingAgent()
        interview_planner_agent = interview_planner_agent or InterviewPlannerAgent()
        question_generator_hr = question_generator_hr or QuestionGeneratorAgent(round_type="HR")
        question_generator_tech = question_generator_tech or QuestionGeneratorAgent(
            round_type="TECHNICAL"
        )
        hr_interview_agent = hr_interview_agent or HRInterviewAgent()
        technical_interview_agent = technical_interview_agent or TechnicalInterviewAgent()
        evaluation_agent_hr = evaluation_agent_hr or EvaluationAgent()
        evaluation_agent_tech = evaluation_agent_tech or EvaluationAgent()
        career_coach_agent = career_coach_agent or CareerCoachAgent()
        report_generator_agent = report_generator_agent or ReportGeneratorAgent()

    nodes = {
        "supervisor": supervisor_node,
        "resume_agent": resume_agent or _stub("resume_agent"),
        "jd_agent": jd_agent or _stub("jd_agent"),
        "ats_agent": ats_agent or _stub("ats_agent"),
        "profile_intelligence_agent": profile_intelligence_agent
        or _stub("profile_intelligence_agent"),
        "competency_mapping_agent": competency_mapping_agent or _stub("competency_mapping_agent"),
        "interview_planner_agent": interview_planner_agent or _stub("interview_planner_agent"),
        "question_generator_hr": question_generator_hr or _stub("question_generator_hr"),
        "hr_interview_agent": hr_interview_agent or _stub("hr_interview_agent"),
        "evaluation_agent_hr": evaluation_agent_hr or _stub("evaluation_agent_hr"),
        "question_generator_tech": question_generator_tech or _stub("question_generator_tech"),
        "technical_interview_agent": technical_interview_agent
        or _stub("technical_interview_agent"),
        "evaluation_agent_tech": evaluation_agent_tech or _stub("evaluation_agent_tech"),
        "policy_node": policy_node_handler or policy_node,
        "tool_executor_node": tool_executor_handler,
        "career_coach_agent": career_coach_agent or _stub("career_coach_agent"),
        "report_generator_agent": report_generator_agent or _stub("report_generator_agent"),
        "report_verification_node": report_verification_handler or report_verification_node,
    }

    graph = StateGraph(InterviewState)

    # ── Register nodes ────────────────────────────────────────
    for name, fn in nodes.items():
        graph.add_node(name, fn)

    # ── Entry point ───────────────────────────────────────────
    graph.set_entry_point("supervisor")

    # ── Linear edges: ingestion pipeline ─────────────────────
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "resume_agent": "resume_agent",
            "jd_agent": "jd_agent",
            "interview_planner_agent": "interview_planner_agent",
            "question_generator_hr": "question_generator_hr",
            "question_generator_tech": "question_generator_tech",
            "hr_interview_agent": "hr_interview_agent",
            "technical_interview_agent": "technical_interview_agent",
            "evaluation_agent_hr": "evaluation_agent_hr",
            "evaluation_agent_tech": "evaluation_agent_tech",
            "policy_node": "policy_node",
            "report_generator_agent": "report_generator_agent",
            "COMPLETED": END,
            "FAILED": END,
        },
    )
    graph.add_edge("resume_agent", "jd_agent")
    graph.add_edge("jd_agent", "ats_agent")
    graph.add_edge("ats_agent", "profile_intelligence_agent")
    graph.add_edge("profile_intelligence_agent", "competency_mapping_agent")
    graph.add_edge("competency_mapping_agent", "interview_planner_agent")

    # ── Conditional edge: planner → first round ───────────────
    graph.add_conditional_edges(
        "interview_planner_agent",
        route_after_planner,
        {
            "question_generator_hr": "question_generator_hr",
            "question_generator_tech": "question_generator_tech",
        },
    )

    # Scoped routing functions bound to this graph's allow_stubs parameter
    def _route_after_qgen_hr(state: InterviewState) -> str:
        return route_after_qgen_hr(state, allow_stubs=allow_stubs)

    def _route_after_qgen_tech(state: InterviewState) -> str:
        return route_after_qgen_tech(state, allow_stubs=allow_stubs)

    def _route_after_policy(state: InterviewState) -> str:
        return route_after_policy(state, allow_stubs=allow_stubs)

    # ── HR round loop ─────────────────────────────────────────
    graph.add_conditional_edges(
        "question_generator_hr",
        _route_after_qgen_hr,
        {
            "hr_interview_agent": "hr_interview_agent",
            END: END,
        },
    )
    graph.add_edge("hr_interview_agent", "evaluation_agent_hr")
    graph.add_conditional_edges(
        "evaluation_agent_hr",
        route_after_hr_evaluation,
        {
            "question_generator_hr": "question_generator_hr",
            "question_generator_tech": "question_generator_tech",
            "career_coach_agent": "career_coach_agent",
            "report_generator_agent": "report_generator_agent",
            END: END,
        },
    )

    # ── Technical round loop with PolicyNode tool loop ────────
    graph.add_conditional_edges(
        "question_generator_tech",
        _route_after_qgen_tech,
        {
            "technical_interview_agent": "technical_interview_agent",
            END: END,
        },
    )
    graph.add_edge("technical_interview_agent", "evaluation_agent_tech")
    graph.add_edge("evaluation_agent_tech", "policy_node")

    # Model-Mediated Policy Node loop: policy_node -> tool_executor -> policy_node OR finish
    graph.add_conditional_edges(
        "policy_node",
        _route_after_policy,
        {
            "tool_executor_node": "tool_executor_node",
            "policy_node": "policy_node",
            "report_generator_agent": "career_coach_agent",
            END: END,
        },
    )
    graph.add_edge("tool_executor_node", "policy_node")

    # ── Post-interview with Evidence Reflection ───────────────
    graph.add_edge("career_coach_agent", "report_generator_agent")
    graph.add_edge("report_generator_agent", "report_verification_node")
    graph.add_edge("report_verification_node", END)

    return graph.compile(checkpointer=checkpointer)
