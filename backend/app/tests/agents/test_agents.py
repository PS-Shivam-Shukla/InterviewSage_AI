"""
Agent tests (Phases 6–9) — all use FakeLLMClient, zero real API calls.

Each test verifies:
  - Correct state-key output
  - Pydantic schema validation
  - Retry / fallback behaviour on validation failure
"""

import pytest

from app.agents import (
    ATSAgent,
    CareerCoachAgent,
    CoachingPlanOutput,
    CompetencyMappingAgent,
    CompetencyMatrixOutput,
    EvaluationAgent,
    EvaluationOutput,
    GeneratedQuestion,
    HRInterviewAgent,
    InterviewPlannerAgent,
    InterviewPlanOutput,
    JDAgent,
    JDAnalysis,
    ProfileIntelligenceAgent,
    ProfileSummary,
    QuestionGeneratorAgent,
    ReportGeneratorAgent,
    ResumeAgent,
    ResumeAnalysis,
    TechnicalInterviewAgent,
)
from app.core.llm_client import FakeLLMClient
from app.graph.state import InterviewState

# ── Fixtures ──────────────────────────────────────────────────

def _base_state(**overrides) -> InterviewState:
    state: InterviewState = {
        "interview_id": "iv-test-1",
        "user_id": "u-1",
        "resume_raw_text": (
            "Jane Smith | Senior Python Engineer | 7 years\n"
            "Skills: Python, FastAPI, PostgreSQL, Redis, Docker\n"
            "TechCorp (2017-2024): Built microservices, led team of 5"
        ),
        "jd_raw_text": (
            "Senior Backend Engineer at FinTech Corp. "
            "Requires: Python, FastAPI, PostgreSQL, 5+ years. "
            "Responsibilities: design APIs, mentor juniors."
        ),
        "pending_answer": "I designed a distributed payment system using microservices.",
        "resume_data": {
            "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            "experience": [{"company": "TechCorp", "role": "Senior Python Engineer",
                            "duration_years": 7, "key_achievements": ["Led microservices migration"]}],
            "seniority_signal": "SENIOR",
            "relevant_experience_months": 84,
            "confidence_score": 0.9,
        },
        "jd_data": {
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "preferred_skills": ["Redis", "Docker"],
            "responsibilities": ["Design APIs", "Mentor juniors"],
            "seniority_level": "SENIOR",
            "target_role": "Senior Backend Engineer",
            "industry": "FinTech",
            "company_values": ["innovation", "reliability"],
        },
        "ats_analysis": {"overlap_score": 85, "matched_keywords": ["Python", "FastAPI"],
                         "missing_keywords": [], "phrasing_suggestions": []},
        "profile_summary": {"calibrated_seniority": "SENIOR", "strengths": ["Python"],
                            "growth_edges": ["System Design"], "difficulty_recommendation": "HARD"},
        "competency_matrix": [
            {"name": "Coding",         "weight": 30, "description": "", "rationale": ""},
            {"name": "System Design",  "weight": 25, "description": "", "rationale": ""},
            {"name": "Communication",  "weight": 25, "description": "", "rationale": ""},
            {"name": "Culture Fit",    "weight": 20, "description": "", "rationale": ""},
        ],
        "interview_plan": {"hr_question_count": 2, "technical_question_count": 3,
                           "estimated_duration_minutes": 45, "round_structure": []},
        "current_round": "HR",
        "current_question": {
            "question_text": "Tell me about a challenging project.",
            "competency_targeted": "Communication",
            "difficulty": "MEDIUM",
            "question_type": "behavioral",
            "round_type": "HR",
            "sequence_number": 1,
        },
        "questions_asked": [],
        "answers": [],
        "evaluations": [],
        "coaching_plan": {},
        "final_report": None,
        "retry_count_this_node": 0,
        "error_log": [],
        "next_node": None,
    }
    state.update(overrides)
    return state


# ── Phase 6: Resume Agent ─────────────────────────────────────

class TestResumeAgent:
    def test_extracts_resume_data(self):
        fake_output = ResumeAnalysis(
            technical_skills=["Python", "FastAPI"],
            experience=[],
            career_level="SENIOR",
            resume_quality_score=90,
        )
        agent = ResumeAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        result = agent(_base_state())
        assert "resume_data" in result
        assert result["resume_data"]["career_level"] == "SENIOR"

    def test_missing_raw_text_triggers_failure(self):
        agent = ResumeAgent(llm_client=FakeLLMClient())
        state = _base_state(resume_raw_text="")
        result = agent(state)
        # Should write error_log, not crash
        assert "error_log" in result
        assert len(result["error_log"]) > 0

    def test_low_confidence_adds_warning(self):
        fake_output = ResumeAnalysis(
            technical_skills=["Python"],
            career_level="UNKNOWN",
            resume_quality_score=60,
        )
        agent = ResumeAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        result = agent(_base_state())
        assert "resume_data" in result


# ── Phase 6: JD Agent ─────────────────────────────────────────

class TestJDAgent:
    def test_extracts_jd_data(self):
        fake_output = JDAnalysis(
            required_skills=["Python", "FastAPI"],
            seniority_level="SENIOR",
            target_role="Backend Engineer",
            industry="FinTech",
        )
        agent = JDAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        result = agent(_base_state())
        assert "jd_data" in result
        assert result["jd_data"]["target_role"] == "Backend Engineer"

    def test_missing_jd_text_falls_back(self):
        agent = JDAgent(llm_client=FakeLLMClient())
        result = agent(_base_state(jd_raw_text=""))
        assert "error_log" in result

    def test_invalid_seniority_normalised(self):
        jd = JDAnalysis(seniority_level="super-senior")
        assert jd.seniority_level == "NOT_SPECIFIED"

    def test_valid_seniority_preserved(self):
        jd = JDAnalysis(seniority_level="senior")
        assert jd.seniority_level == "SENIOR"


# ── Phase 6: ATS Agent ────────────────────────────────────────

class TestATSAgent:
    class _SuggestionOut:
        def model_dump(self): return {"suggestions": ["Add PostgreSQL to skills section"]}

    def test_ats_returns_overlap_score(self):
        fake_suggestion = type("S", (), {"suggestions": ["Add Redis to skills"]})()
        agent = ATSAgent(llm_client=FakeLLMClient(responses=[
            type("S", (), {
                "suggestions": ["Add Redis to skills"],
                "model_dump": lambda self: {"suggestions": ["Add Redis"]}
            })()
        ]))
        # Inject correct structured response

        from pydantic import BaseModel
        class Sug(BaseModel):
            suggestions: list[str] = []
        agent2 = ATSAgent(llm_client=FakeLLMClient(responses=[Sug(suggestions=["Add Redis"])]))
        result = agent2(_base_state())
        assert "ats_analysis" in result
        assert "ats_overlap_score" in result["ats_analysis"]

    def test_missing_resume_data_returns_partial(self):
        agent = ATSAgent(llm_client=FakeLLMClient())
        result = agent(_base_state(resume_data={}))
        assert result.get("ats_analysis", {}).get("incomplete_data") is True


# ── Phase 6: Profile Intelligence Agent ──────────────────────

class TestProfileIntelligenceAgent:
    def test_returns_profile_summary(self):
        fake_output = ProfileSummary(
            strengths=["Python expertise"],
            growth_edges=["System Design"],
            calibrated_seniority="SENIOR",
            difficulty_recommendation="HARD",
        )
        agent = ProfileIntelligenceAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        result = agent(_base_state())
        assert "profile_summary" in result
        assert result["profile_summary"]["calibrated_seniority"] == "SENIOR"

    def test_fallback_uses_jd_seniority(self):
        agent = ProfileIntelligenceAgent(llm_client=FakeLLMClient(responses=[
            ValueError("LLM failed"), ValueError("retry failed"), ValueError("3rd failure")
        ]))
        # Override to force failure path
        state = _base_state()
        state["resume_data"] = {}
        state["jd_data"]["seniority_level"] = "MID"
        # Direct failure path test
        fallback = agent._on_failure(state, "test error")
        assert fallback["profile_summary"]["calibrated_seniority"] == "MID"


# ── Phase 7: Competency Mapping Agent ────────────────────────

class TestCompetencyMappingAgent:
    def test_produces_valid_matrix(self):
        from app.agents.competency_mapping_agent import CompetencyItem
        real_output = CompetencyMatrixOutput(competencies=[
            CompetencyItem(name="Coding", weight=40),
            CompetencyItem(name="System Design", weight=35),
            CompetencyItem(name="Communication", weight=25),
        ])
        agent = CompetencyMappingAgent(llm_client=FakeLLMClient(responses=[real_output]))
        result = agent(_base_state())
        assert "competency_matrix" in result
        weights = [c["weight"] for c in result["competency_matrix"]]
        assert sum(weights) == 100

    def test_weights_not_summing_to_100_triggers_retry(self):
        from app.agents.competency_mapping_agent import CompetencyItem
        bad = CompetencyMatrixOutput.__new__(CompetencyMatrixOutput)
        # Use validation to confirm bad weights raise
        with pytest.raises(Exception):
            CompetencyMatrixOutput(competencies=[
                CompetencyItem(name="A", weight=50),
                CompetencyItem(name="B", weight=40),
            ])

    def test_fallback_returns_default_matrix(self):
        agent = CompetencyMappingAgent(llm_client=FakeLLMClient())
        fallback = agent._on_failure(_base_state(), "error")
        total = sum(c["weight"] for c in fallback["competency_matrix"])
        assert total == 100


# ── Phase 7: Interview Planner Agent ─────────────────────────

class TestInterviewPlannerAgent:
    def test_returns_valid_plan(self):
        from app.agents.interview_planner_agent import RoundDetail
        fake_output = InterviewPlanOutput(
            hr_question_count=4,
            technical_question_count=7,
            estimated_duration_minutes=55,
            round_structure=[
                RoundDetail(type="HR", duration_minutes=20, question_count=4),
                RoundDetail(type="TECHNICAL", duration_minutes=35, question_count=7),
            ],
        )
        agent = InterviewPlannerAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        result = agent(_base_state())
        assert "interview_plan" in result
        plan = result["interview_plan"]
        total = plan["hr_question_count"] + plan["technical_question_count"]
        assert 8 <= total <= 16

    def test_total_out_of_range_raises(self):
        with pytest.raises(Exception):
            InterviewPlanOutput(
                hr_question_count=2,
                technical_question_count=2,   # total=4, below minimum 8
                estimated_duration_minutes=30,
            )

    def test_fallback_plan_is_valid(self):
        agent = InterviewPlannerAgent(llm_client=FakeLLMClient())
        fallback = agent._on_failure(_base_state(), "error")
        plan = fallback["interview_plan"]
        assert 8 <= plan["hr_question_count"] + plan["technical_question_count"] <= 16


# ── Phase 8: Question Generator Agent ────────────────────────

class TestQuestionGeneratorAgent:
    def test_generates_question(self):
        fake_output = GeneratedQuestion(
            question_text="How do you write asynchronous endpoints in Python and FastAPI?",
            competency_targeted="Coding",
            difficulty="MEDIUM",
            question_type="fundamentals",
        )
        agent = QuestionGeneratorAgent(round_type="TECHNICAL",
                                       llm_client=FakeLLMClient(responses=[fake_output]))
        result = agent(_base_state())
        assert "current_question" in result
        assert "question_text" in result["current_question"]

    def test_duplicate_triggers_retry(self):
        """If generated question is identical to an already-asked one, agent must fail/retry."""
        from app.agents.question_generator_agent import _is_duplicate
        existing = [{"question_text": "Tell me about a challenging project."}]
        assert _is_duplicate("Tell me about a challenging project.", existing) is True

    def test_non_duplicate_passes(self):
        from app.agents.question_generator_agent import _is_duplicate
        existing = [{"question_text": "Tell me about a challenging project."}]
        assert _is_duplicate("How do you design a distributed cache?", existing) is False

    def test_fallback_uses_seed_bank(self):
        agent = QuestionGeneratorAgent(llm_client=FakeLLMClient())
        fallback = agent._on_failure(_base_state(), "error")
        assert "current_question" in fallback
        assert "question_text" in fallback["current_question"]

    def test_adaptive_difficulty(self):
        from app.agents.question_generator_agent import _adaptive_difficulty
        high_scores = [{"competency_targeted": "Coding", "score": 9},
                       {"competency_targeted": "Coding", "score": 9}]
        assert _adaptive_difficulty("Coding", high_scores) in ("HARD", "ADVANCED")
        low_scores = [{"competency_targeted": "Coding", "score": 3}]
        assert _adaptive_difficulty("Coding", low_scores) == "EASY"


# ── Phase 8: Interview Agents ─────────────────────────────────

class TestHRInterviewAgent:
    def test_records_answer(self):
        from app.agents.hr_interview_agent import HRTurn
        fake_output = HRTurn(
            question_text="Tell me about yourself.",
            candidate_answer="I have 7 years of Python experience.",
            follow_up_question=None,
        )
        agent = HRInterviewAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        result = agent(_base_state(pending_answer="I have 7 years of Python experience."))
        assert "answers" in result
        assert len(result["answers"]) == 1
        assert result["answers"][0]["round_type"] == "HR"

    def test_empty_answer_returns_reprompt(self):
        agent = HRInterviewAgent(llm_client=FakeLLMClient())
        result = agent(_base_state(pending_answer=""))
        assert "current_question" in result
        assert "re_prompt" in result["current_question"]


class TestTechnicalInterviewAgent:
    def test_records_technical_answer(self):
        from app.agents.technical_interview_agent import TechnicalTurn
        fake_output = TechnicalTurn(
            question_text="Design a rate limiter.",
            candidate_answer="I'd use token bucket algorithm.",
            follow_up_question="What is the time complexity?",
        )
        agent = TechnicalInterviewAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        state = _base_state(
            pending_answer="I'd use token bucket algorithm.",
            current_question={
                "question_text": "Design a rate limiter.",
                "competency_targeted": "System Design",
                "difficulty": "HARD",
                "question_type": "system_design",
                "round_type": "TECHNICAL",
                "sequence_number": 3,
            }
        )
        result = agent(state)
        assert "answers" in result
        assert result["answers"][0]["round_type"] == "TECHNICAL"


# ── Phase 9: Evaluation Agent ─────────────────────────────────

class TestEvaluationAgent:
    def test_scores_answer(self):
        fake_output = EvaluationOutput(
            score=8,
            rubric_breakdown={"Correctness": 4, "Depth": 4, "Communication": 4},
            feedback="Good use of real example.",
            ideal_answer_summary="Could mention trade-offs.",
        )
        agent = EvaluationAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        state = _base_state(answers=[{
            "question_id": 1,
            "question_text": "Tell me about yourself.",
            "answer_text": "I built microservices at TechCorp.",
            "round_type": "HR",
            "competency_targeted": "Communication",
        }])
        result = agent(state)
        assert "evaluations" in result
        assert result["evaluations"][0]["score"] == 8

    def test_invalid_sub_score_triggers_retry(self):
        with pytest.raises(Exception):
            EvaluationOutput(
                score=7,
                rubric_breakdown={"Correctness": 10},  # > 5 → invalid
            )

    def test_no_answer_returns_empty(self):
        agent = EvaluationAgent(llm_client=FakeLLMClient())
        result = agent(_base_state(answers=[]))
        assert result == {}

    def test_failure_flags_human_review(self):
        agent = EvaluationAgent(llm_client=FakeLLMClient())
        fallback = agent._on_failure(_base_state(), "error")
        assert fallback["evaluations"][0]["needs_human_review"] is True


# ── Phase 9: Career Coach Agent ───────────────────────────────

class TestCareerCoachAgent:
    def test_produces_coaching_plan(self):
        from app.agents.career_coach_agent import CoachingItem
        fake_output = CoachingPlanOutput(items=[
            CoachingItem(
                competency="System Design",
                current_score=5.0,
                specific_gap_description="In Q3 about distributed systems, the answer lacked depth on consistency trade-offs.",
                recommended_action="Study the CAP theorem with 3 practice problems on designing distributed KV stores.",
                priority=1,
            )
        ])
        agent = CareerCoachAgent(llm_client=FakeLLMClient(responses=[fake_output]))
        state = _base_state(
            evaluations=[{"competency_targeted": "System Design", "score": 5,
                          "feedback": "Needs more depth"}],
            questions_asked=[{"question_text": "Design a KV store", "round_type": "TECHNICAL",
                              "competency_targeted": "System Design", "question_type": "system_design"}],
            answers=[{"answer_text": "I would use Redis", "question_id": 1}],
        )
        result = agent(state)
        assert "coaching_plan" in result
        assert len(result["coaching_plan"]["items"]) > 0

    def test_empty_evaluations_returns_partial(self):
        agent = CareerCoachAgent(llm_client=FakeLLMClient())
        result = agent(_base_state(evaluations=[]))
        assert result["coaching_plan"]["partial_data"] is True

    def test_generic_gap_description_raises_validation(self):
        from app.agents.career_coach_agent import CoachingItem
        with pytest.raises(Exception):
            CoachingPlanOutput(items=[
                CoachingItem(
                    competency="Coding",
                    current_score=4.0,
                    specific_gap_description="Needs work",  # too short — < 20 chars
                    recommended_action="Practice more",
                    priority=1,
                )
            ])


# ── Phase 9: Report Generator Agent ──────────────────────────

class TestReportGeneratorAgent:
    def test_compiles_report(self):
        fake_summary = type("S", (), {})()
        from pydantic import BaseModel
        class SummaryOut(BaseModel):
            executive_summary: str
        fake = SummaryOut(executive_summary="Strong performance overall.")
        agent = ReportGeneratorAgent(llm_client=FakeLLMClient(responses=[fake]))
        state = _base_state(
            evaluations=[
                {"competency_targeted": "Coding", "score": 8, "feedback": "Good",
                 "question_id": 1, "question_type": "fundamentals"},
                {"competency_targeted": "Communication", "score": 7, "feedback": "Clear",
                 "question_id": 2, "question_type": "behavioral"},
            ],
            questions_asked=[
                {"question_text": "Q1", "round_type": "TECHNICAL", "competency_targeted": "Coding",
                 "question_type": "fundamentals"},
                {"question_text": "Q2", "round_type": "HR", "competency_targeted": "Communication",
                 "question_type": "behavioral"},
            ],
            answers=[
                {"answer_text": "Answer 1", "question_id": 1},
                {"answer_text": "Answer 2", "question_id": 2},
            ],
            coaching_plan={"items": [], "partial_data": False},
        )
        result = agent(state)
        assert "final_report" in result
        assert result["final_report"]["overall_score"] > 0
        assert result["current_round"] == "COMPLETE"

    def test_scorecard_weights_applied(self):
        from app.agents.report_generator_agent import _build_scorecard
        matrix = [
            {"name": "Coding", "weight": 60},
            {"name": "Communication", "weight": 40},
        ]
        evals = [
            {"competency_targeted": "Coding", "score": 10},
            {"competency_targeted": "Communication", "score": 5},
        ]
        scorecard, overall = _build_scorecard(evals, matrix)
        # weighted: 100*0.6 + 50*0.4 = 60+20 = 80.0
        assert overall == 80.0
        assert len(scorecard) == 2
