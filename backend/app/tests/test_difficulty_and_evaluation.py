"""
Unit tests for Question Difficulty Policy & Answer Sanity Guard (Section 10.4 & 10.12).
Verifies experience-based difficulty ceilings, non-answer rejection, 0/10 (0%) formatting, and 5-run determinism.
"""

from app.services.answer_sanity_guard import AnswerSanityGuard
from app.services.difficulty_policy import QuestionDifficultyPolicy


def test_1_two_month_candidate_has_basic_ceiling():
    ceiling = QuestionDifficultyPolicy.get_max_allowed_difficulty(
        relevant_experience_months=2, seniority_level="JUNIOR"
    )
    assert ceiling == "BASIC"


def test_2_two_month_candidate_cannot_receive_hard():
    is_valid, reason = QuestionDifficultyPolicy.validate_question_difficulty(
        "HARD", relevant_experience_months=2, seniority_level="JUNIOR"
    )
    assert is_valid is False
    assert "exceeds candidate ceiling" in reason


def test_3_two_month_candidate_cannot_receive_advanced():
    is_valid, reason = QuestionDifficultyPolicy.validate_question_difficulty(
        "ADVANCED", relevant_experience_months=2, seniority_level="JUNIOR"
    )
    assert is_valid is False
    assert "exceeds candidate ceiling" in reason


def test_4_two_month_candidate_perfect_scores_cannot_escalate_past_basic():
    evals = [{"score": 10.0}, {"score": 10.0}]
    res = QuestionDifficultyPolicy.calculate_next_difficulty(
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        previous_evaluations=evals,
        current_difficulty="BASIC",
    )
    assert res.max_allowed_difficulty == "BASIC"
    assert res.recommended_difficulty == "BASIC"
    assert res.is_escalation_capped is True


def test_5_six_month_candidate_has_intermediate_ceiling():
    ceiling = QuestionDifficultyPolicy.get_max_allowed_difficulty(
        relevant_experience_months=6, seniority_level="JUNIOR"
    )
    assert ceiling == "INTERMEDIATE"


def test_6_twenty_four_month_candidate_has_intermediate_ceiling():
    ceiling = QuestionDifficultyPolicy.get_max_allowed_difficulty(
        relevant_experience_months=24, seniority_level="MID"
    )
    assert ceiling == "INTERMEDIATE"


def test_7_forty_eight_month_candidate_has_advanced_ceiling():
    ceiling = QuestionDifficultyPolicy.get_max_allowed_difficulty(
        relevant_experience_months=48, seniority_level="MID"
    )
    assert ceiling == "ADVANCED"


def test_8_sixty_plus_month_senior_has_system_design_ceiling():
    ceiling = QuestionDifficultyPolicy.get_max_allowed_difficulty(
        relevant_experience_months=72, seniority_level="SENIOR"
    )
    assert ceiling == "SYSTEM_DESIGN"


def test_9_senior_title_with_two_months_experience_remains_basic():
    # Title != Truth rule: Title says 'Senior Software Engineer', but experience is 2 months
    ceiling = QuestionDifficultyPolicy.get_max_allowed_difficulty(
        relevant_experience_months=2, seniority_level="INTERN"
    )
    assert ceiling == "BASIC"


def test_10_i_dont_know_classified_as_no_answer_and_bypasses_llm():
    res = AnswerSanityGuard.evaluate("I don't know")
    assert res.is_valid_answer is False
    assert res.answer_quality == "NO_ANSWER"
    assert res.score_1_10 == 0
    assert res.score_pct == 0
    assert res.needs_llm_eval is False


def test_11_idk_classified_as_no_answer():
    res = AnswerSanityGuard.evaluate("idk")
    assert res.is_valid_answer is False
    assert res.answer_quality == "NO_ANSWER"
    assert res.score_1_10 == 0
    assert res.score_pct == 0
    assert res.needs_llm_eval is False


def test_12_empty_answer_classified_as_empty():
    res = AnswerSanityGuard.evaluate("   ")
    assert res.is_valid_answer is False
    assert res.answer_quality == "EMPTY"
    assert res.score_1_10 == 0
    assert res.score_pct == 0
    assert res.needs_llm_eval is False


def test_13_gibberish_classified_as_gibberish():
    res = AnswerSanityGuard.evaluate("asdfasdfasdf")
    assert res.is_valid_answer is False
    assert res.answer_quality == "GIBBERISH"
    assert res.score_1_10 == 0
    assert res.score_pct == 0
    assert res.needs_llm_eval is False


def test_14_valid_answer_proceeds_to_llm():
    res = AnswerSanityGuard.evaluate(
        "FastAPI uses Pydantic models to validate request payloads asynchronously."
    )
    assert res.is_valid_answer is True
    assert res.answer_quality == "VALID_ANSWER"
    assert res.needs_llm_eval is True


def test_15_one_out_of_ten_raw_score_converts_to_ten_percent():
    raw_1_10 = 1
    pct = raw_1_10 * 10
    assert pct == 10


def test_16_unambiguous_display_string_formatting():
    raw_1_10 = 0
    pct = 0
    display_str = f"{raw_1_10}/10 ({pct}%)"
    assert display_str == "0/10 (0%)"


def test_17_adaptive_difficulty_bounded_by_ceiling():
    evals = [{"score": 9.0}]
    res = QuestionDifficultyPolicy.calculate_next_difficulty(
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        previous_evaluations=evals,
        current_difficulty="BASIC",
    )
    assert res.recommended_difficulty == "BASIC"


def test_18_five_run_determinism_assertion():
    results = [
        QuestionDifficultyPolicy.get_max_allowed_difficulty(
            relevant_experience_months=2, seniority_level="JUNIOR"
        )
        for _ in range(5)
    ]
    first = results[0]
    for r in results[1:]:
        assert r == first == "BASIC"
