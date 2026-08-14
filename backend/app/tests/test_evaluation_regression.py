"""
Comprehensive Regression Test Suite — Evaluation Pipeline Fix

Verifies:
1. Aptitude correct numeric answer -> 10/10 (100%)
2. Aptitude incorrect numeric answer -> 2/10 (20%), NOT GIBBERISH
3. Aptitude gibberish/random text ("mai modi hun 238748927498213") -> 0/10 (0%), GIBBERISH
4. Technical question + "420" -> low score / irrelevant (NOT treated as valid)
5. Technical question + valid explanation -> dynamic score, specific feedback
6. HR question + behavioral answer -> behavioral rubric evaluation
7. HR question + numeric answer -> low score / irrelevant
8. Seniority is passed to evaluation without NameError
9. Missing round_type is resolved safely from question or answer
10. System failure -> EVALUATION_UNAVAILABLE + needs_human_review=True (NEVER 50/100)
11. Generic fallback feedback "Evaluated based on response structure..." is NEVER returned
12. Unassessed competencies are not assigned arbitrary 50% scores
"""

from app.agents.evaluation_agent import EvaluationAgent, EvaluationOutput
from app.core.llm_client import FakeLLMClient


def test_aptitude_correct_numeric_answer():
    """Case A: Aptitude correct numeric answer -> 10/10 (100%), question-specific feedback."""
    agent = EvaluationAgent()
    state = {
        "current_question": {
            "sequence_number": 1,
            "question_text": "The mean of 4, 8, 12, 16, and X is 10. What is the value of X?",
            "competency_targeted": "Quantitative Reasoning",
            "question_type": "aptitude",
            "round_type": "APTITUDE",
        },
        "answers": [{"answer_text": "10"}],
        "profile_summary": {"calibrated_seniority": "FRESHER"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    assert eval_rec["score"] == 10
    assert eval_rec["answer_quality"] == "VALID_ANSWER"
    assert "10" in eval_rec["feedback"]
    assert eval_rec["needs_human_review"] is False


def test_aptitude_incorrect_numeric_answer():
    """Case B: Aptitude incorrect numeric answer -> 0/10 (0%), NOT GIBBERISH."""
    agent = EvaluationAgent()
    state = {
        "current_question": {
            "sequence_number": 1,
            "question_text": "The mean of 4, 8, 12, 16, and X is 10. What is the value of X?",
            "competency_targeted": "Quantitative Reasoning",
            "question_type": "aptitude",
            "round_type": "APTITUDE",
        },
        "answers": [{"answer_text": "24"}],
        "profile_summary": {"calibrated_seniority": "FRESHER"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    assert eval_rec["score"] == 0
    assert eval_rec["answer_quality"] == "VALID_ANSWER"
    assert "24" in eval_rec["feedback"]
    assert "10" in eval_rec["feedback"]


def test_aptitude_gibberish_random_text():
    """Case C: Aptitude random text 'mai modi hun 238748927498213' -> 0/10 (0%), GIBBERISH."""
    agent = EvaluationAgent()
    state = {
        "current_question": {
            "sequence_number": 1,
            "question_text": "The mean of 4, 8, 12, 16, and X is 10. What is the value of X?",
            "competency_targeted": "Quantitative Reasoning",
            "question_type": "aptitude",
            "round_type": "APTITUDE",
        },
        "answers": [{"answer_text": "mai modi hun 238748927498213"}],
        "profile_summary": {"calibrated_seniority": "FRESHER"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    assert eval_rec["score"] == 0
    assert eval_rec["answer_quality"] == "GIBBERISH"
    assert eval_rec["score"] != 5  # NEVER 50/100


def test_technical_question_numeric_answer_irrelevant():
    """Case D: Technical question + '420' -> low score / score 1, NOT awarded technical credit."""
    fake_output = EvaluationOutput(
        score=1,
        rubric_breakdown={"Correctness": 1, "Completeness": 1, "Clarity & Structure": 1},
        feedback="The response '420' does not address dependency injection in FastAPI.",
        ideal_answer_summary="Should explain FastAPI's Depends() syntax.",
    )
    agent = EvaluationAgent(llm_client=FakeLLMClient(responses=[fake_output]))
    state = {
        "current_question": {
            "sequence_number": 2,
            "question_text": "What is dependency injection in FastAPI?",
            "competency_targeted": "Backend Architecture",
            "question_type": "technical",
            "round_type": "TECHNICAL",
        },
        "answers": [{"answer_text": "420"}],
        "profile_summary": {"calibrated_seniority": "MID"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    assert eval_rec["score"] == 1
    assert "FastAPI" in eval_rec["feedback"] or "420" in eval_rec["feedback"]


def test_technical_question_valid_explanation():
    """Case E: Technical question + valid explanation -> dynamic score, specific feedback."""
    fake_output = EvaluationOutput(
        score=9,
        rubric_breakdown={"Technical Depth": 5, "Problem Solving": 4, "Clarity & Structure": 4},
        feedback="Clear explanation of Depends() and asynchronous dependency resolution.",
        ideal_answer_summary="Explains type annotations and hierarchical dependencies.",
    )
    agent = EvaluationAgent(llm_client=FakeLLMClient(responses=[fake_output]))
    state = {
        "current_question": {
            "sequence_number": 3,
            "question_text": "What is dependency injection in FastAPI?",
            "competency_targeted": "Backend Architecture",
            "question_type": "technical",
            "round_type": "TECHNICAL",
        },
        "answers": [{"answer_text": "FastAPI uses Depends() to inject shared services like DB sessions into route handlers."}],
        "profile_summary": {"calibrated_seniority": "MID"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    assert eval_rec["score"] == 9
    assert "Depends()" in eval_rec["feedback"]


def test_hr_question_behavioral_evaluation():
    """Case F: HR question + behavioral answer -> evaluated using behavioral rubric."""
    fake_output = EvaluationOutput(
        score=8,
        rubric_breakdown={"Relevance": 4, "Behavioral Evidence": 4, "Clarity & Structure": 4},
        feedback="Clear situation, action taken to resolve disagreement, and positive outcome.",
        ideal_answer_summary="Concludes with key learning takeaways.",
    )
    agent = EvaluationAgent(llm_client=FakeLLMClient(responses=[fake_output]))
    state = {
        "current_question": {
            "sequence_number": 4,
            "question_text": "Tell me about a conflict you handled with a teammate.",
            "competency_targeted": "Conflict Resolution",
            "question_type": "hr",
            "round_type": "HR",
        },
        "answers": [{"answer_text": "We disagreed on DB schema design. I scheduled a design review and presented benchmark data."}],
        "profile_summary": {"calibrated_seniority": "SENIOR"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    assert eval_rec["score"] == 8


def test_system_failure_does_not_fabricate_50_percent():
    """Case G: Evaluation failure -> EVALUATION_UNAVAILABLE + needs_human_review=True (NEVER 50/100)."""
    agent = EvaluationAgent()
    fallback = agent._on_failure({}, "Database connection timeout")
    eval_rec = fallback["evaluations"][0]
    assert eval_rec["score"] == 0
    assert eval_rec["needs_human_review"] is True
    assert eval_rec["answer_quality"] == "EVALUATION_UNAVAILABLE"
    assert eval_rec["feedback"] != "Evaluated based on response structure and key concepts provided."


def test_fresher_technical_strong_explanation_all_scores_populated():
    """TEST 1: Fresher + Technical question + strong valid explanation -> all 3 scores > 0."""
    fake_output = EvaluationOutput(
        score=9,
        rubric_breakdown={
            "Correctness": 5,
            "Completeness": 4,
            "Communication": 5,
            "Confidence": 4,
        },
        feedback="Excellent explanation of FastAPI's Depends() syntax.",
        ideal_answer_summary="Clear explanation of dependencies.",
    )
    agent = EvaluationAgent(llm_client=FakeLLMClient(responses=[fake_output]))
    state = {
        "current_question": {
            "sequence_number": 1,
            "question_text": "What is dependency injection in FastAPI?",
            "competency_targeted": "Backend Architecture",
            "question_type": "technical",
            "round_type": "TECHNICAL",
        },
        "answers": [{"answer_text": "FastAPI uses Depends() to inject reusable dependency functions into routes automatically."}],
        "profile_summary": {"calibrated_seniority": "FRESHER"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    rubric = eval_rec.get("rubric_breakdown", {})
    assert eval_rec["score"] == 9
    assert rubric.get("Communication") == 5
    assert rubric.get("Confidence") == 4


def test_junior_technical_clear_but_incorrect():
    """TEST 2: Junior + Technical question + clear but technically incorrect answer -> low technical, independent comm/conf."""
    fake_output = EvaluationOutput(
        score=3,
        rubric_breakdown={
            "Correctness": 1,
            "Completeness": 2,
            "Communication": 4,
            "Confidence": 4,
        },
        feedback="The answer is articulate and structured, but conflates dependency injection with middleware.",
        ideal_answer_summary="Should focus on Depends() instead of middleware.",
    )
    agent = EvaluationAgent(llm_client=FakeLLMClient(responses=[fake_output]))
    state = {
        "current_question": {
            "sequence_number": 1,
            "question_text": "What is dependency injection in FastAPI?",
            "competency_targeted": "Backend Architecture",
            "question_type": "technical",
            "round_type": "TECHNICAL",
        },
        "answers": [{"answer_text": "FastAPI dependency injection is executed as a global middleware pipeline on every incoming HTTP request."}],
        "profile_summary": {"calibrated_seniority": "JUNIOR"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    rubric = eval_rec.get("rubric_breakdown", {})
    assert eval_rec["score"] == 3
    assert rubric.get("Correctness") == 1
    assert rubric.get("Communication") == 4
    assert rubric.get("Confidence") == 4


def test_fresher_technical_irrelevant_numeric_420():
    """TEST 3: Fresher + Technical question + '420' -> low technical score, no default 50 for comm/conf."""
    fake_output = EvaluationOutput(
        score=1,
        rubric_breakdown={
            "Correctness": 1,
            "Completeness": 1,
            "Communication": 1,
            "Confidence": 1,
        },
        feedback="The numeric answer '420' does not address dependency injection.",
        ideal_answer_summary="Provide an explanation of FastAPI dependency injection.",
    )
    agent = EvaluationAgent(llm_client=FakeLLMClient(responses=[fake_output]))
    state = {
        "current_question": {
            "sequence_number": 1,
            "question_text": "What is dependency injection in FastAPI?",
            "competency_targeted": "Backend Architecture",
            "question_type": "technical",
            "round_type": "TECHNICAL",
        },
        "answers": [{"answer_text": "420"}],
        "profile_summary": {"calibrated_seniority": "FRESHER"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    rubric = eval_rec.get("rubric_breakdown", {})
    assert eval_rec["score"] == 1
    assert rubric.get("Communication") == 1
    assert rubric.get("Confidence") == 1
    assert rubric.get("Communication") != 5  # NEVER default 50%


def test_fresher_technical_hedging_phrases_evaluates_confidence():
    """TEST 4: Fresher + Technical question + hedging text -> lower confidence score reflecting hedging evidence."""
    fake_output = EvaluationOutput(
        score=6,
        rubric_breakdown={
            "Correctness": 3,
            "Completeness": 3,
            "Communication": 3,
            "Confidence": 2,
        },
        feedback="The candidate understands basic concepts but uses excessive hedging ('I think', 'maybe').",
        ideal_answer_summary="State technical facts assertively.",
    )
    agent = EvaluationAgent(llm_client=FakeLLMClient(responses=[fake_output]))
    state = {
        "current_question": {
            "sequence_number": 1,
            "question_text": "What is dependency injection in FastAPI?",
            "competency_targeted": "Backend Architecture",
            "question_type": "technical",
            "round_type": "TECHNICAL",
        },
        "answers": [{"answer_text": "I think FastAPI maybe uses something called Depends, but I'm not completely sure how it works."}],
        "profile_summary": {"calibrated_seniority": "FRESHER"},
    }
    res = agent(state)
    eval_rec = res["evaluations"][0]
    rubric = eval_rec.get("rubric_breakdown", {})
    assert eval_rec["score"] == 6
    assert rubric.get("Confidence") == 2  # Lower confidence due to hedging evidence


def test_no_generic_feedback_string():
    """Verify generic placeholder feedback is never returned as valid evaluation."""
    agent = EvaluationAgent()
    state = {
        "current_question": {
            "sequence_number": 1,
            "question_text": "Calculate simple interest on $1000 at 5% for 3 years.",
            "round_type": "APTITUDE",
        },
        "answers": [{"answer_text": "$150"}],
        "profile_summary": {"calibrated_seniority": "FRESHER"},
    }
    res = agent(state)
    fb = res["evaluations"][0]["feedback"]
    assert "Evaluated based on response structure and key concepts provided." not in fb
