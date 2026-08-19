"""
Master LangGraph Workflow Engine for InterviewSage AI.
Integrates DISE, AI Kernel, PostgreSQL Checkpointer, and Node Tracing & Observability (Sprint 7).
"""

from __future__ import annotations

import time
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.core.logging import get_logger
from app.core.metrics import GRAPH_EXECUTION_SECONDS
from app.graph.state import GraphState, InterviewState
from app.kernel.context_builder import ContextBuilder
from app.kernel.guardrails import Guardrails
from app.kernel.model_router import ModelRouter
from app.kernel.prompt_manager import PromptManager
from app.kernel.structured_output import StructuredOutputParser
from app.strategy.blueprint_generator import BlueprintGenerator
from app.strategy.classifier import CandidateClassifier
from app.strategy.difficulty_engine import DifficultyEngine

logger = get_logger(__name__)

# Shared singleton engines
classifier = CandidateClassifier()
blueprint_generator = BlueprintGenerator()
difficulty_engine = DifficultyEngine()
prompt_manager = PromptManager()
context_builder = ContextBuilder()
guardrails = Guardrails()
model_router = ModelRouter()
structured_output_parser = StructuredOutputParser()


def get_checkpointer(database_url: str | None = None) -> BaseCheckpointSaver:
    """
    Factory function providing persistent checkpointer instance:
    PostgresSaver for PostgreSQL database using ConnectionPool,
    or MemorySaver fallback for SQLite / test environments.
    """
    url = database_url or settings.database_url
    if not url or url.startswith("sqlite") or ":memory:" in url:
        logger.info("Initializing LangGraph MemorySaver for SQLite/Test environment.")
        return MemorySaver()

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg_pool import ConnectionPool

        pool = ConnectionPool(url, min_size=1, max_size=10, open=True, timeout=2.0)
        pool.wait(timeout=2.0)
        saver = PostgresSaver(pool)
        logger.info(f"Initialized LangGraph PostgresSaver for database pool: {url.split('@')[-1]}")
        return saver
    except Exception as exc:
        logger.warning(f"PostgresSaver connection pool fallback to MemorySaver: {exc}")
        return MemorySaver()


# ─────────────────────────────────────────────────────────────
# Node Handlers with Execution Tracing & Metrics
# ─────────────────────────────────────────────────────────────


def classify_candidate_node(state: GraphState) -> dict[str, Any]:
    """Node: Runs Candidate Classification Engine with execution timing and metrics."""
    start_t = time.perf_counter()
    logger.info("LangGraph Node Started: classify_candidate_node")
    try:
        resume_json = state.get("resume_json") or state.get("resume_data") or {}
        skill_graph = state.get("skill_graph") or {}

        classification = classifier.classify(resume_json, skill_graph)
        duration_ms = int((time.perf_counter() - start_t) * 1000)
        GRAPH_EXECUTION_SECONDS.labels(node_name="classify_candidate", status="success").observe(
            duration_ms / 1000.0
        )

        logger.info(
            "LangGraph Node Finished: classify_candidate_node",
            extra={"duration_ms": duration_ms, "workflow_stage": "CLASSIFIED"},
        )

        return {
            "classification": {
                "tier": classification.tier,
                "level": classification.level,
                "vector_scores": classification.vector_scores,
                "summary": classification.summary_reasoning,
            },
            "workflow_stage": "CLASSIFIED",
        }
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_t) * 1000)
        GRAPH_EXECUTION_SECONDS.labels(node_name="classify_candidate", status="error").observe(
            duration_ms / 1000.0
        )
        logger.error(
            f"LangGraph Node Failed: classify_candidate_node: {exc}",
            exc_info=True,
            extra={"duration_ms": duration_ms},
        )
        raise


def generate_blueprint_node(state: GraphState) -> dict[str, Any]:
    """Node: Runs DISE Blueprint Generator with execution timing and metrics."""
    start_t = time.perf_counter()
    logger.info("LangGraph Node Started: generate_blueprint_node")
    try:
        classification_data = state.get("classification") or {}
        tier = classification_data.get("tier", "Mid-Level Engineer")
        level = classification_data.get("level", 3)

        from app.strategy.classifier import CandidateClassification

        class_obj = CandidateClassification(
            tier=tier,
            level=level,
            vector_scores=classification_data.get("vector_scores", {}),
            summary_reasoning=classification_data.get("summary", ""),
        )

        jd_json = state.get("jd_json") or state.get("jd_data") or {}
        blueprint = blueprint_generator.generate(class_obj, jd_json)

        blueprint_dict = {
            "candidate_tier": blueprint.candidate_tier,
            "candidate_level": blueprint.candidate_level,
            "total_duration_minutes": blueprint.total_duration_minutes,
            "total_questions": blueprint.total_questions,
            "blueprint_items": [
                {
                    "sequence_number": item.sequence_number,
                    "category": item.category,
                    "target_difficulty": item.target_difficulty,
                    "allocated_minutes": item.allocated_minutes,
                    "weight_percentage": item.weight_percentage,
                    "primary_focus_area": item.primary_focus_area,
                }
                for item in blueprint.blueprint_items
            ],
        }

        duration_ms = int((time.perf_counter() - start_t) * 1000)
        GRAPH_EXECUTION_SECONDS.labels(node_name="generate_blueprint", status="success").observe(
            duration_ms / 1000.0
        )

        logger.info(
            "LangGraph Node Finished: generate_blueprint_node",
            extra={"duration_ms": duration_ms, "workflow_stage": "BLUEPRINT_GENERATED"},
        )

        return {
            "interview_blueprint": blueprint_dict,
            "workflow_stage": "BLUEPRINT_GENERATED",
            "human_review_required": True,
        }
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_t) * 1000)
        GRAPH_EXECUTION_SECONDS.labels(node_name="generate_blueprint", status="error").observe(
            duration_ms / 1000.0
        )
        logger.error(
            f"LangGraph Node Failed: generate_blueprint_node: {exc}",
            exc_info=True,
            extra={"duration_ms": duration_ms},
        )
        raise


def personalize_question_node(state: GraphState) -> dict[str, Any]:
    """Node: Personalizes baseline question template using AI Kernel."""
    start_t = time.perf_counter()
    logger.info("LangGraph Node Started: personalize_question_node")
    try:
        blueprint = state.get("interview_blueprint") or {}
        items = blueprint.get("blueprint_items", [])
        questions_asked = state.get("questions_asked") or []

        seq = len(questions_asked) + 1
        target_item = items[seq - 1] if seq <= len(items) else (items[-1] if items else None)

        cat = target_item["category"] if target_item else "General Technical"
        diff = target_item["target_difficulty"] if target_item else 3
        focus = target_item["primary_focus_area"] if target_item else "Software Engineering"

        resume_json = state.get("resume_json") or {}
        projects = resume_json.get("projects", [])
        proj_desc = (
            projects[0].get("description", "general projects") if projects else "general projects"
        )

        masked_context, _ = guardrails.mask_pii(proj_desc)

        rendered = prompt_manager.render(
            "prompt:question_personalizer:v1",
            {
                "seniority_level": state.get("classification", {}).get("tier", "Engineer"),
                "target_competency": cat,
                "project_context": masked_context,
                "baseline_question": f"Discuss your architectural approach to {focus}.",
            },
        )

        current_q = {
            "sequence_number": seq,
            "category": cat,
            "target_difficulty": diff,
            "question_text": rendered["user"],
        }

        duration_ms = int((time.perf_counter() - start_t) * 1000)
        GRAPH_EXECUTION_SECONDS.labels(node_name="personalize_question", status="success").observe(
            duration_ms / 1000.0
        )

        logger.info(
            "LangGraph Node Finished: personalize_question_node",
            extra={"duration_ms": duration_ms, "workflow_stage": "QUESTION_READY"},
        )

        return {
            "current_question": current_q,
            "workflow_stage": "QUESTION_READY",
        }
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_t) * 1000)
        GRAPH_EXECUTION_SECONDS.labels(node_name="personalize_question", status="error").observe(
            duration_ms / 1000.0
        )
        logger.error(
            f"LangGraph Node Failed: personalize_question_node: {exc}",
            exc_info=True,
            extra={"duration_ms": duration_ms},
        )
        raise


def evaluate_answer_node(state: GraphState) -> dict[str, Any]:
    """Node: Evaluates candidate answer via EvaluationAgent and runs real-time difficulty adaptation."""
    start_t = time.perf_counter()
    logger.info("LangGraph Node Started: evaluate_answer_node")
    try:
        from app.agents.evaluation_agent import EvaluationAgent

        eval_agent = EvaluationAgent()
        eval_dict = eval_agent(state)

        duration_ms = int((time.perf_counter() - start_t) * 1000)
        GRAPH_EXECUTION_SECONDS.labels(node_name="evaluate_answer", status="success").observe(
            duration_ms / 1000.0
        )

        logger.info(
            "LangGraph Node Finished: evaluate_answer_node",
            extra={"duration_ms": duration_ms, "workflow_stage": "ANSWER_EVALUATED"},
        )

        return eval_dict
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_t) * 1000)
        GRAPH_EXECUTION_SECONDS.labels(node_name="evaluate_answer", status="error").observe(
            duration_ms / 1000.0
        )
        logger.error(
            f"LangGraph Node Failed: evaluate_answer_node: {exc}",
            exc_info=True,
            extra={"duration_ms": duration_ms},
        )
        raise


def route_next_step(state: GraphState) -> str:
    """Conditional Edge Router."""
    blueprint = state.get("interview_blueprint") or {}
    total_target = blueprint.get("total_questions", 5)
    evaluations = state.get("evaluations") or []

    if len(evaluations) >= total_target:
        return "end"
    return "personalize_question"


# ─────────────────────────────────────────────────────────────
# Master Graph Builder
# ─────────────────────────────────────────────────────────────


def build_master_workflow(checkpointer: BaseCheckpointSaver | None = None) -> Any:
    """Assembles master execution graph combining DISE, AI Kernel, Checkpointer, and Observability."""
    from app.graph.graph_builder import build_graph

    if checkpointer is None:
        checkpointer = get_checkpointer()

    return build_graph(allow_stubs=False, checkpointer=checkpointer)
