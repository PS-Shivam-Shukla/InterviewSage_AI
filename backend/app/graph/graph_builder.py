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

from langgraph.graph import END, StateGraph

from app.agents.supervisor_agent import SupervisorAgent
from app.graph.state import InterviewState

_supervisor = SupervisorAgent()


def supervisor_node(state: InterviewState) -> dict:
    """Supervisor node handler — inspects state and updates next_node and workflow_stage."""
    next_node = _supervisor.decide_next_step(state)
    return {
        "next_node": next_node,
        "workflow_stage": state.get("workflow_stage", "INITIALIZING"),
    }


def route_after_supervisor(state: InterviewState) -> str:
    """Entry & hub routing powered by SupervisorAgent decision engine."""
    return _supervisor.decide_next_step(state)


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
      - Advance to technical round.
    """
    plan = state.get("interview_plan") or {}
    hr_target = plan.get("hr_question_count", 5)
    hr_asked = sum(1 for q in (state.get("questions_asked") or []) if q.get("round_type") == "HR")
    if hr_asked < hr_target:
        return "question_generator_hr"
    return "question_generator_tech"


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


def route_after_policy(state: InterviewState) -> str:
    """Dynamic router after PolicyNode decision."""
    return state.get("next_node") or "report_generator_agent"


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
    allow_stubs: bool = True,
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
        "supervisor": _stub("supervisor"),
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
        {"resume_agent": "resume_agent"},
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

    # ── HR round loop ─────────────────────────────────────────
    graph.add_edge("question_generator_hr", "hr_interview_agent")
    graph.add_edge("hr_interview_agent", "evaluation_agent_hr")
    graph.add_conditional_edges(
        "evaluation_agent_hr",
        route_after_hr_evaluation,
        {
            "question_generator_hr": "question_generator_hr",
            "question_generator_tech": "question_generator_tech",
        },
    )

    # ── Technical round loop with PolicyNode tool loop ────────
    graph.add_edge("question_generator_tech", "technical_interview_agent")
    graph.add_edge("technical_interview_agent", "evaluation_agent_tech")
    graph.add_edge("evaluation_agent_tech", "policy_node")

    # Model-Mediated Policy Node loop: policy_node -> tool_executor -> policy_node OR finish
    graph.add_conditional_edges(
        "policy_node",
        route_after_policy,
        {
            "tool_executor_node": "tool_executor_node",
            "report_generator_agent": "career_coach_agent",
        },
    )
    graph.add_edge("tool_executor_node", "policy_node")

    # ── Post-interview with Evidence Reflection ───────────────
    graph.add_edge("career_coach_agent", "report_generator_agent")
    graph.add_edge("report_generator_agent", "report_verification_node")
    graph.add_edge("report_verification_node", END)

    return graph.compile()
