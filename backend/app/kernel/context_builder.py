from __future__ import annotations

from typing import Any


class ContextBuilder:
    """
    Context & Token Budget Management Subsystem.
    Enforces maximum token allocation per task to prevent context window overflow
    and lost-in-the-middle degradation.
    """

    DEFAULT_WINDOW_BUDGET = 8192

    def __init__(self, total_budget: int = DEFAULT_WINDOW_BUDGET) -> None:
        self.total_budget = total_budget

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count using baseline 4 chars per token approximation.
        Fast, deterministic, zero-dependency tokenizer fallback.
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def allocate_budget(self, task_type: str = "question_personalization") -> dict[str, int]:
        """
        Return component token allocation budget for a given task type.
        """
        if task_type == "answer_evaluation":
            return {
                "system_budget": 800,
                "candidate_context_budget": 1000,
                "memory_budget": 2000,
                "knowledge_budget": 2000,
                "output_budget": 1500,
                "safety_reserve": 892,
            }
        elif task_type == "report_synthesis":
            return {
                "system_budget": 1000,
                "candidate_context_budget": 3000,
                "memory_budget": 0,
                "knowledge_budget": 2000,
                "output_budget": 1500,
                "safety_reserve": 692,
            }
        else:  # Default: question_personalization
            return {
                "system_budget": 500,
                "candidate_context_budget": 1500,
                "memory_budget": 1000,
                "knowledge_budget": 1500,
                "output_budget": 1000,
                "safety_reserve": 2192,
            }

    def prune_text_to_budget(self, text: str, max_tokens: int) -> str:
        """
        Greedily prune text to fit within specified max token count.
        """
        current_tokens = self.estimate_tokens(text)
        if current_tokens <= max_tokens:
            return text

        # Rough character cut: max_tokens * 4 chars
        max_chars = max_tokens * 4
        pruned = text[:max_chars]
        
        # Trim to last complete word boundary
        last_space = pruned.rfind(" ")
        if last_space > 0:
            pruned = pruned[:last_space]
            
        return pruned + " ... [trimmed to fit context budget]"

    def prepare_context_payload(
        self,
        system_text: str,
        candidate_context: str,
        memory_history: list[str],
        knowledge_snippets: list[str],
        task_type: str = "question_personalization",
    ) -> dict[str, Any]:
        """
        Assemble trimmed, token-budget compliant payload for prompt rendering.
        """
        budgets = self.allocate_budget(task_type)

        trimmed_system = self.prune_text_to_budget(system_text, budgets["system_budget"])
        trimmed_candidate = self.prune_text_to_budget(candidate_context, budgets["candidate_context_budget"])
        
        # Combine memory history
        combined_memory = "\n".join(memory_history) if memory_history else ""
        trimmed_memory = self.prune_text_to_budget(combined_memory, budgets["memory_budget"])

        # Combine knowledge snippets
        combined_knowledge = "\n".join(knowledge_snippets) if knowledge_snippets else ""
        trimmed_knowledge = self.prune_text_to_budget(combined_knowledge, budgets["knowledge_budget"])

        total_input_tokens = (
            self.estimate_tokens(trimmed_system)
            + self.estimate_tokens(trimmed_candidate)
            + self.estimate_tokens(trimmed_memory)
            + self.estimate_tokens(trimmed_knowledge)
        )

        return {
            "system_text": trimmed_system,
            "candidate_context": trimmed_candidate,
            "memory_text": trimmed_memory,
            "knowledge_text": trimmed_knowledge,
            "estimated_input_tokens": total_input_tokens,
            "allocated_output_tokens": budgets["output_budget"],
            "within_budget": total_input_tokens <= (self.total_budget - budgets["output_budget"]),
        }
