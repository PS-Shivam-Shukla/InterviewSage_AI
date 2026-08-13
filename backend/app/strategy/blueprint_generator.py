from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from app.strategy.classifier import CandidateClassification


@dataclass
class QuestionBlueprintItem:
    sequence_number: int
    category: str
    target_difficulty: int  # 1 (Easy) to 5 (Advanced)
    allocated_minutes: int
    weight_percentage: float
    primary_focus_area: str


@dataclass
class InterviewBlueprint:
    candidate_tier: str
    candidate_level: int
    total_duration_minutes: int
    total_questions: int
    blueprint_items: list[QuestionBlueprintItem] = field(default_factory=list)


class BlueprintGenerator:
    """
    Deterministic Interview Blueprint Generator (DISE Module).
    Constructs candidate-tailored blueprints establishing question counts, categories,
    time budgets, scoring weights, and target difficulty curves.
    """

    def generate(
        self,
        classification: CandidateClassification,
        jd_json: dict[str, Any],
        duration_minutes: int = 60,
        recruiter_overrides: dict[str, Any] | None = None,
    ) -> InterviewBlueprint:
        """
        Generate custom Interview Blueprint based on candidate seniority level.
        """
        level = classification.level

        # Baseline Strategy Allocation per Seniority Level
        if level <= 2:  # Intern / Junior
            total_questions = 6
            categories = [
                ("Resume Project Deep Dive", 2, 8, 20.0, "Academic / Entry Project"),
                ("Programming Fundamentals", 2, 8, 25.0, "Syntax & Data Structures"),
                ("Framework Knowledge", 2, 10, 25.0, "Framework Components"),
                ("Coding Problem Solving", 3, 15, 20.0, "Practical Algorithm"),
                ("Behavioral & Soft Skills", 2, 7, 10.0, "Teamwork & Learning"),
            ]
        elif level <= 4:  # Mid / Senior Engineer
            total_questions = 6
            categories = [
                ("Resume Project Deep Dive", 3, 10, 20.0, "High-Impact Project Probe"),
                ("Language Internals", 4, 8, 15.0, "Memory & Concurrency"),
                ("System Design & Scale", 4, 20, 35.0, "Distributed Architecture"),
                ("Database & Concurrency", 3, 10, 15.0, "Data Integrity & Indexing"),
                ("Behavioral & Leadership", 3, 7, 15.0, "Ownership & Conflict"),
            ]
        else:  # Staff / Principal / Manager
            total_questions = 5
            categories = [
                ("System Architecture & Vision", 5, 20, 40.0, "Enterprise System Design"),
                ("Resilience & Failure Modes", 5, 12, 25.0, "Fault Tolerance & SLAs"),
                ("Technical Vision & RFCs", 4, 10, 15.0, "Tech Stack Evaluation"),
                ("Behavioral & Mentorship", 4, 10, 20.0, "Cross-Team Leadership"),
            ]

        # Apply Recruiter Overrides if present
        if recruiter_overrides and "duration" in recruiter_overrides:
            duration_minutes = int(recruiter_overrides["duration"])

        items: list[QuestionBlueprintItem] = []
        for idx, (cat, diff, mins, weight, focus) in enumerate(categories, start=1):
            items.append(
                QuestionBlueprintItem(
                    sequence_number=idx,
                    category=cat,
                    target_difficulty=diff,
                    allocated_minutes=mins,
                    weight_percentage=weight,
                    primary_focus_area=focus,
                )
            )

        return InterviewBlueprint(
            candidate_tier=classification.tier,
            candidate_level=classification.level,
            total_duration_minutes=duration_minutes,
            total_questions=len(items),
            blueprint_items=items,
        )
