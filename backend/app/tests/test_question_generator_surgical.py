"""
Surgical Question Generation Regression Tests.
Verifies:
1. Competency correctness (C/C++ does not generate SQL primary/foreign keys).
2. Python competency relevance.
3. Difficulty propagation (INTERMEDIATE candidate difficulty preserved).
4. History awareness and duplicate avoidance.
5. Placeholder protection rejection ([RAG], [PostgreSQL], etc.).
6. Question type diversity.
7. Existing GeneratedQuestion schema contract compatibility.
"""

from app.agents.question_generator_agent import GeneratedQuestion, QuestionGeneratorAgent
from app.services.difficulty_policy import QuestionDifficultyPolicy
from app.services.question_relevance_service import (
    QuestionRelevanceResult,
    QuestionRelevanceService,
)


def test_question_generator_schema_contract_compatibility():
    q = GeneratedQuestion(
        question_text="Explain the concept of virtual functions and vtables in C++.",
        competency_targeted="C/C++",
        difficulty="INTERMEDIATE",
        question_type="fundamentals",
        personalisation_note="Targeted based on C++ resume experience.",
    )
    assert q.question_text.startswith("Explain")
    assert q.competency_targeted == "C/C++"
    assert q.difficulty == "INTERMEDIATE"
    assert q.question_type == "fundamentals"


def test_competency_correctness_sql_rejected_for_cpp():
    res: QuestionRelevanceResult = QuestionRelevanceService.validate_question(
        question_text="Explain the difference between a primary key and a foreign key in a relational database.",
        question_difficulty="INTERMEDIATE",
        relevant_experience_months=36,
        seniority_level="MID",
        candidate_skills=["C/C++", "C++"],
        work_experience_bullets=["Developed C++ multi-threaded backend services."],
        jd_required_skills=["C/C++"],
        questions_asked=[],
        round_type="technical",
        competency_targeted="C/C++",
    )
    assert res.accepted is False
    assert "Competency Mismatch" in res.reason or "GATE 6 FAILED" in res.reason


def test_placeholder_protection_rejection():
    res: QuestionRelevanceResult = QuestionRelevanceService.validate_question(
        question_text="How does your experience with [RAG] frameworks optimize large-scale processing in [PostgreSQL]?",
        question_difficulty="INTERMEDIATE",
        relevant_experience_months=36,
        seniority_level="MID",
        candidate_skills=["Python"],
        work_experience_bullets=["Built Python web applications."],
        jd_required_skills=["Python"],
        questions_asked=[],
        round_type="technical",
        competency_targeted="Python",
    )
    assert res.accepted is False
    assert "Unresolved Placeholder" in res.reason or "GATE 0 FAILED" in res.reason


def test_difficulty_propagation_mid_candidate():
    policy_res = QuestionDifficultyPolicy.calculate_next_difficulty(
        relevant_experience_months=36,
        seniority_level="MID",
        previous_evaluations=[{"score": 8}],
        current_difficulty="INTERMEDIATE",
    )
    assert policy_res.recommended_difficulty in {"INTERMEDIATE", "ADVANCED"}
    assert policy_res.recommended_difficulty != "BASIC"


def test_history_awareness_duplicate_avoidance():
    previous = [
        {
            "question_text": "What is the difference between a list and a tuple in Python?",
            "competency_targeted": "Python",
        }
    ]
    res: QuestionRelevanceResult = QuestionRelevanceService.validate_question(
        question_text="What is the difference between a list and a tuple in Python?",
        question_difficulty="INTERMEDIATE",
        relevant_experience_months=36,
        seniority_level="MID",
        candidate_skills=["Python"],
        work_experience_bullets=["Python backend development"],
        jd_required_skills=["Python"],
        questions_asked=previous,
        round_type="technical",
        competency_targeted="Python",
    )
    assert res.accepted is False
    assert (
        "Paraphrase Duplicate" in res.reason
        or "GATE 5 FAILED" in res.reason
        or "too similar" in res.reason.lower()
    )


def test_question_generator_agent_execution_cpp(mocker):
    mocker.patch.object(
        QuestionGeneratorAgent,
        "_invoke_structured",
        return_value=GeneratedQuestion(
            question_text="How do smart pointers manage memory ownership in modern C++?",
            competency_targeted="C/C++",
            difficulty="INTERMEDIATE",
            question_type="fundamentals",
            personalisation_note="Targeted based on low-latency C++ experience.",
        ),
    )
    agent = QuestionGeneratorAgent(round_type="TECHNICAL")
    state = {
        "resume_data": {
            "skills": ["C/C++", "C++", "Linux", "Data Structures"],
            "seniority_signal": "MID",
            "relevant_experience_months": 36,
            "experience": [{"description": "Developed low-latency C++ network engine"}],
        },
        "jd_data": {
            "target_role": "C++ Systems Engineer",
            "required_skills": ["C/C++", "Linux"],
        },
        "competency_matrix": [{"name": "C/C++", "weight": 100}],
        "questions_asked": [],
        "evaluations": [],
    }
    result = agent._run(state)
    curr_q = result.get("current_question", {})

    assert curr_q.get("question_text") is not None
    assert "primary key" not in curr_q.get("question_text", "").lower()
    assert "foreign key" not in curr_q.get("question_text", "").lower()
    assert "[" not in curr_q.get("question_text", "")
    assert "]" not in curr_q.get("question_text", "")


def test_question_generator_agent_execution_hr(mocker):
    """Verify that HR round_type generates HR questions with HR competencies and passes Gate 2."""
    mocker.patch.object(
        QuestionGeneratorAgent,
        "_invoke_structured",
        return_value=GeneratedQuestion(
            question_text="Tell me about a time you had a conflict with a teammate on a deadline and how you resolved it.",
            competency_targeted="Conflict Resolution & Adaptability",
            difficulty="MEDIUM",
            question_type="behavioral",
            personalisation_note="Evaluates soft skills and team collaboration.",
        ),
    )
    agent = QuestionGeneratorAgent(round_type="HR")
    state = {
        "resume_data": {
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "seniority_signal": "MID",
            "relevant_experience_months": 36,
            "experience": [{"description": "Backend engineer at tech startup"}],
        },
        "jd_data": {
            "target_role": "Backend Engineer",
            "required_skills": ["Python", "FastAPI"],
        },
        "competency_matrix": [{"name": "Python", "weight": 50}, {"name": "FastAPI", "weight": 50}],
        "questions_asked": [],
        "evaluations": [],
    }
    result = agent._run(state)
    curr_q = result.get("current_question", {})

    assert curr_q.get("question_text") is not None
    assert "conflict" in curr_q.get("question_text", "").lower()
    assert curr_q.get("competency_targeted") in {
        "Leadership & Team Collaboration",
        "Conflict Resolution & Adaptability",
        "Work Ethic & Ownership",
        "Culture Fit & Career Growth",
    }


def test_multi_angle_retry_stays_on_same_competency(mocker):
    """Verify that retries rotate cognitive angles on the SAME target competency before switching."""
    agent = QuestionGeneratorAgent(round_type="TECHNICAL")
    state = {
        "resume_data": {
            "skills": ["React", "TypeScript"],
            "seniority_signal": "MID",
            "relevant_experience_months": 24,
            "experience": [{"description": "Frontend developer building React apps"}],
        },
        "jd_data": {
            "target_role": "Frontend Engineer",
            "required_skills": ["React", "TypeScript"],
        },
        "competency_matrix": [
            {"name": "React", "weight": 70},
            {"name": "TypeScript", "weight": 30},
        ],
        "target_competency": "React",
        "questions_asked": [],
        "evaluations": [],
    }

    # Attempt 1: PRIMARY
    mocker.patch.object(
        QuestionGeneratorAgent,
        "_invoke_structured",
        return_value=GeneratedQuestion(
            question_text="Explain React components and JSX syntax.",
            competency_targeted="React",
            difficulty="MEDIUM",
            question_type="fundamentals",
        ),
    )
    res1 = agent._run(state)
    assert res1["current_question"]["competency_targeted"] == "React"
    assert res1["current_question"]["cognitive_angle"] == "fundamentals_and_concepts"

    # Attempt 2 retry: ALTERNATIVE_ANGLE on SAME competency (React)
    mocker.patch.object(
        QuestionGeneratorAgent,
        "_invoke_structured",
        return_value=GeneratedQuestion(
            question_text="How would you implement custom hooks in React for API fetching?",
            competency_targeted="React",
            difficulty="MEDIUM",
            question_type="fundamentals",
        ),
    )
    res2 = agent._run(state, retry_feedback="[ATTEMPT 1 FAILED] [strategy=PRIMARY] Question was too similar.")
    assert res2["current_question"]["competency_targeted"] == "React"
    assert res2["current_question"]["cognitive_angle"] == "implementation_and_usage"

    # Attempt 3 retry: ALTERNATIVE_ANGLE on SAME competency (React)
    mocker.patch.object(
        QuestionGeneratorAgent,
        "_invoke_structured",
        return_value=GeneratedQuestion(
            question_text="How do you diagnose and debug memory leaks caused by uncleared event listeners in React?",
            competency_targeted="React",
            difficulty="MEDIUM",
            question_type="fundamentals",
        ),
    )
    res3 = agent._run(state, retry_feedback="[ATTEMPT 2 FAILED] [strategy=ALTERNATIVE_ANGLE] Question failed relevance.")
    assert res3["current_question"]["competency_targeted"] == "React"
    assert res3["current_question"]["cognitive_angle"] == "debugging_and_failure_investigation"


def test_seed_bank_fallback_recovery_preserves_competency():
    """Verify that when LLM retries are exhausted, _on_failure returns a valid seed question."""
    agent = QuestionGeneratorAgent(round_type="TECHNICAL")
    state = {
        "resume_data": {
            "skills": ["React"],
            "seniority_signal": "MID",
        },
        "jd_data": {
            "target_role": "Frontend Engineer",
            "required_skills": ["React"],
        },
        "competency_matrix": [{"name": "React", "weight": 100}],
        "questions_asked": [],
        "target_competency": "React",
    }

    fallback_res = agent._on_failure(state, error="LLM call timed out")
    curr_q = fallback_res.get("current_question")
    assert curr_q is not None
    assert curr_q.get("question_text")
    assert curr_q.get("competency_targeted") == "React"
    assert curr_q.get("round_type") == "TECHNICAL"
    assert curr_q.get("fallback_used") is True
    assert curr_q.get("fallback_type") == "seed_bank"
    assert len(fallback_res.get("error_log", [])) == 1


def test_interview_service_accepts_seed_bank_fallback(mocker):
    """Verify that InterviewService._generate_question_via_llm accepts seed-bank recovered questions."""
    from app.services.interview_service import InterviewService

    mocker.patch.object(
        QuestionGeneratorAgent,
        "__call__",
        return_value={
            "current_question": {
                "question_text": "Explain the core architectural principles and standard implementation patterns for React.",
                "competency_targeted": "React",
                "difficulty": "MEDIUM",
                "question_type": "fundamentals",
                "round_type": "TECHNICAL",
                "sequence_number": 1,
                "fallback_used": True,
                "fallback_type": "seed_bank",
            },
            "error_log": [{"agent": "QuestionGeneratorAgent", "error": "LLM failed", "fallback": "seed_bank"}],
        },
    )

    dummy_db = mocker.MagicMock()
    service = InterviewService(dummy_db)
    result = service._generate_question_via_llm(
        round_type="TECHNICAL",
        resume_data={"skills": ["React"], "seniority_signal": "MID"},
        jd_data={"target_role": "Frontend Engineer", "required_skills": ["React"]},
        competency_matrix=[{"name": "React", "weight": 100}],
        questions_asked=[],
        evaluations=[],
    )

    assert result is not None
    assert result["question_text"] == "Explain the core architectural principles and standard implementation patterns for React."
    assert result["competency_targeted"] == "React"
    assert result["fallback_used"] is True

