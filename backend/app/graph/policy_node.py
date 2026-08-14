"""
Model-Mediated Policy Node (Phase 1).
Central decision-making component that executes the perceive -> decide -> tool_call -> observe -> repeat/finish loop.

Design contract:
- Receives InterviewState, available MCP tool definitions, past observations, and iteration count.
- Evaluates machine-readable tool schemas via structured LLM prompt.
- Emits either a ToolCallDecision or FinishDecision.
- Enforces MAX_POLICY_ITERATIONS = 5 iteration boundary to prevent infinite loops.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

from app.core.llm_client import LLMClient
from app.core.logging import get_logger
from app.graph.state import InterviewState

logger = get_logger(__name__)

MAX_POLICY_ITERATIONS = 5


# ── Structured Decision Schemas ───────────────────────────────────────────────

class ToolCallDecision(BaseModel):
    """LLM decision to invoke a specific registered MCP tool."""
    action: Literal["tool_call"] = "tool_call"
    tool: str = Field(description="Name of the registered MCP tool to invoke.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments matching tool parameters schema.")
    reasoning: str = Field(default="", description="Chain-of-thought rationale for selecting this tool.")


class FinishDecision(BaseModel):
    """LLM decision that tool execution loop is complete."""
    action: Literal["finish"] = "finish"
    result: Dict[str, Any] = Field(default_factory=dict, description="Final decision result or summary.")
    reasoning: str = Field(default="", description="Rationale for finishing policy execution.")


class PolicyDecision(BaseModel):
    """Discriminated union container for PolicyNode decision."""
    action: Literal["tool_call", "finish"]
    tool_call: Optional[ToolCallDecision] = None
    finish: Optional[FinishDecision] = None
    reasoning: str = ""

    @model_validator(mode="after")
    def validate_action_payload(self) -> "PolicyDecision":
        if self.action == "tool_call" and not self.tool_call:
            raise ValueError("Action 'tool_call' requires a valid tool_call payload.")
        if self.action == "finish" and not self.finish:
            # Auto-populate default finish payload if omitted
            self.finish = FinishDecision(reasoning=self.reasoning)
        return self


# ── Policy Node Implementation ────────────────────────────────────────────────

class PolicyNode:
    """
    Model-mediated policy decision engine for LangGraph execution.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client or LLMClient(temperature=0.1)

    def __call__(self, state: InterviewState) -> dict:
        """LangGraph node entry point for model-mediated tool loop."""
        iteration = state.get("policy_iteration_count", 0) + 1
        interview_id = state.get("interview_id", "N/A")

        # ── 1. Bounded Loop Enforcement ───────────────────────────────────────
        if iteration > MAX_POLICY_ITERATIONS:
            logger.warning(
                f"⚠️ [POLICY NODE] Max iteration limit reached ({iteration - 1}/{MAX_POLICY_ITERATIONS}) for interview {interview_id}. "
                "Terminating policy loop safely."
            )
            finish_dec = FinishDecision(
                reasoning=f"Max policy iteration limit ({MAX_POLICY_ITERATIONS}) reached.",
                result={"status": "MAX_ITERATIONS_REACHED"},
            )
            return {
                "policy_iteration_count": iteration,
                "policy_decisions": [{"action": "finish", "tool": None, "reasoning": finish_dec.reasoning}],
                "next_node": "report_generator_agent",
            }

        # ── 2. Discover / Fetch exposed MCP Tool Schemas ──────────────────────
        tools_list = state.get("available_tools") or []
        if not tools_list:
            from app.mcp import mcp_server
            tools_list = mcp_server.list_tools()

        # ── 3. Render Tool Schemas & Previous Observations ────────────────────
        tool_schemas_str = "\n".join([
            f"- Tool Name: '{t.get('name')}'\n"
            f"  Description: {t.get('description')}\n"
            f"  Parameters: {t.get('parameters')}\n"
            f"  Required Arguments: {t.get('required')}"
            for t in tools_list
        ])

        observations = state.get("observations") or []
        obs_str = "\n".join([
            f"Turn {i+1}: Tool '{o.get('tool_name')}' -> Success: {o.get('success')} | Output: {str(o.get('output'))[:200]} | Error: {o.get('error')}"
            for i, o in enumerate(observations[-5:])   # last 5 observations
        ]) if observations else "None"

        current_q = state.get("current_question") or {}
        answers = state.get("answers") or []
        latest_ans = answers[-1].get("answer_text", "") if answers else ""

        system_prompt = (
            "You are the central Policy Orchestrator for InterviewSage AI.\n"
            "Your job is to inspect candidate answers, available MCP tool definitions, and past observations, "
            "and decide the next action: invoke a tool ('tool_call') OR finish execution ('finish').\n\n"
            "CRITICAL RULES:\n"
            "1. You MUST dynamically choose the appropriate tool based on tool schemas.\n"
            "2. If an answer needs rubric scoring, select 'score_answer_rubric'.\n"
            "3. If candidate details are required, select 'get_candidate_profile' or 'retrieve_job_requirements'.\n"
            "4. If a follow-up question is needed, select 'generate_followup_question'.\n"
            "5. If sufficient evaluation and turn processing has been performed, emit action='finish'."
        )

        user_prompt = (
            f"Iteration: {iteration}/{MAX_POLICY_ITERATIONS}\n"
            f"Current Question: {current_q.get('question_text', 'N/A')}\n"
            f"Latest Candidate Answer:\n{latest_ans}\n\n"
            f"AVAILABLE MCP TOOL SCHEMAS:\n{tool_schemas_str}\n\n"
            f"PREVIOUS OBSERVATIONS:\n{obs_str}\n\n"
            "Decide the next action: return JSON matching PolicyDecision schema."
        )

        logger.info(
            f"\n================================================================================\n"
            f"🤖 [POLICY NODE STARTED] Iteration: {iteration}/{MAX_POLICY_ITERATIONS} | Available Tools: {[t.get('name') for t in tools_list]}\n"
            f"────────────────────────────────────────────────────────────────────────────────"
        )

        # ── 4. Invoke Structured LLM Decision ─────────────────────────────────
        messages = LLMClient.build_messages(
            system_prompt=system_prompt,
            developer_prompt="Return JSON matching PolicyDecision schema with action='tool_call' or 'finish'.",
            user_content=user_prompt,
        )

        try:
            decision: PolicyDecision = self.llm.invoke_structured(messages, PolicyDecision)
        except Exception as exc:
            logger.warning(f"PolicyNode structured invocation failed: {exc}. Falling back to default turn finish.")
            decision = PolicyDecision(
                action="finish",
                finish=FinishDecision(reasoning="Fallback decision on LLM error"),
                reasoning=str(exc),
            )

        # ── 5. Format Output State Update & Telemetry Log ─────────────────────
        if decision.action == "tool_call" and decision.tool_call:
            chosen_tool = decision.tool_call.tool
            tool_args = decision.tool_call.arguments
            reasoning = decision.tool_call.reasoning

            logger.info(
                f"🤖 [POLICY DECISION] Action: tool_call | Chosen Tool: '{chosen_tool}'\n"
                f"   Reasoning: {reasoning}\n"
                f"================================================================================"
            )

            return {
                "policy_iteration_count": iteration,
                "policy_decisions": [{
                    "action": "tool_call",
                    "tool": chosen_tool,
                    "arguments": tool_args,
                    "reasoning": reasoning,
                    "iteration": iteration,
                }],
                "available_tools": tools_list,
                "next_node": "tool_executor_node",
            }
        else:
            reasoning = decision.finish.reasoning if decision.finish else decision.reasoning
            logger.info(
                f"🤖 [POLICY DECISION] Action: finish\n"
                f"   Reasoning: {reasoning}\n"
                f"================================================================================"
            )

            return {
                "policy_iteration_count": iteration,
                "policy_decisions": [{
                    "action": "finish",
                    "tool": None,
                    "reasoning": reasoning,
                    "iteration": iteration,
                }],
                "available_tools": tools_list,
                "next_node": "report_generator_agent",
            }


# Node instance helper
policy_node = PolicyNode()
