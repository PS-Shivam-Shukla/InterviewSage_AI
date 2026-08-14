"""
Unit tests for Question Relevance & Hybrid Validation Service (Section 10.6).
Verifies skill classification, tech entity normalization, paraphrase duplicate detection,
hard difficulty gates, and 5-run determinism.
"""

from app.services.difficulty_policy import QuestionDifficultyPolicy
from app.services.question_relevance_service import (
    LexicalSimilarityEngine,
    QuestionRelevanceService,
    TechEntityNormalizer,
)


def test_1_fastapi_experience_classified_as_strong_match():
    classified = QuestionRelevanceService.classify_skills(
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built production REST APIs using FastAPI and Python for 2 months."],
        jd_required_skills=["Python", "FastAPI"],
    )
    assert classified["FastAPI"].tier == "STRONG_MATCH"
    assert classified["FastAPI"].weight == 1.0


def test_2_skill_list_only_fastapi_classified_as_possible_match():
    classified = QuestionRelevanceService.classify_skills(
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Implemented Python scripts for data processing."],
        jd_required_skills=["Python", "FastAPI"],
    )
    assert classified["FastAPI"].tier == "POSSIBLE_MATCH"
    assert classified["FastAPI"].weight == 0.6


def test_3_kubernetes_jd_only_classified_as_jd_gap():
    classified = QuestionRelevanceService.classify_skills(
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI", "Kubernetes"],
    )
    assert classified["Kubernetes"].tier == "JD_GAP"
    assert classified["Kubernetes"].weight == 0.4


def test_4_react_for_python_candidate_classified_as_unrelated():
    res = QuestionRelevanceService.validate_question(
        question_text="Explain React reconciliation and Virtual DOM diffing.",
        question_difficulty="BASIC",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI"],
        questions_asked=[],
    )
    assert res.accepted is False
    assert "Unrelated Tech" in res.reason or res.skill_tier == "UNRELATED"


def test_5_postgres_normalization():
    norm = TechEntityNormalizer.normalize_entity("postgres")
    assert norm == "PostgreSQL"


def test_6_js_normalization():
    norm = TechEntityNormalizer.normalize_entity("js")
    assert norm == "JavaScript"


def test_7_ts_normalization():
    norm = TechEntityNormalizer.normalize_entity("ts")
    assert norm == "TypeScript"


def test_8_paraphrase_duplicate_detection():
    q1 = "What is dependency injection in FastAPI?"
    q2 = "Can you explain how FastAPI's dependency injection mechanism works?"
    score, _ = LexicalSimilarityEngine.compute_hybrid_duplicate_score(q1, [{"question_text": q2}])
    assert score > 0.35  # Detects paraphrase similarity


def test_9_exact_duplicate_detection():
    q = "What is a primary key in PostgreSQL?"
    score, matched = LexicalSimilarityEngine.compute_hybrid_duplicate_score(
        q, [{"question_text": "What is a primary key in PostgreSQL?"}]
    )
    assert score >= 0.99
    assert matched == q


def test_10_different_questions_are_not_duplicates():
    q1 = "What is dependency injection in FastAPI?"
    q2 = "How do indexes optimize query performance in PostgreSQL?"
    score, _ = LexicalSimilarityEngine.compute_hybrid_duplicate_score(
        q1, [{"question_text": q2}]
    )
    assert score < 0.40


def test_11_two_month_candidate_cannot_receive_hard():
    res = QuestionRelevanceService.validate_question(
        question_text="Design a distributed FastAPI microservices system for 100k requests per second.",
        question_difficulty="HARD",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built REST APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI"],
        questions_asked=[],
    )
    assert res.accepted is False
    assert res.difficulty_allowed is False


def test_12_two_month_candidate_cannot_receive_advanced():
    res = QuestionRelevanceService.validate_question(
        question_text="Explain internal query optimization execution plans in PostgreSQL at scale.",
        question_difficulty="ADVANCED",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built REST APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI"],
        questions_asked=[],
    )
    assert res.accepted is False
    assert res.difficulty_allowed is False


def test_13_ten_out_of_ten_performance_cannot_bypass_basic_ceiling():
    policy_res = QuestionDifficultyPolicy.calculate_next_difficulty(
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        previous_evaluations=[{"score": 10.0}],
        current_difficulty="BASIC",
    )
    assert policy_res.recommended_difficulty == "BASIC"
    assert policy_res.max_allowed_difficulty == "BASIC"


def test_14_strong_experience_question_accepted():
    res = QuestionRelevanceService.validate_question(
        question_text="How do path parameters work in FastAPI?",
        question_difficulty="BASIC",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built REST APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI"],
        questions_asked=[],
    )
    assert res.accepted is True
    assert res.skill_tier == "STRONG_MATCH"


def test_15_unrelated_technology_rejected():
    res = QuestionRelevanceService.validate_question(
        question_text="What are Spring Boot starters?",
        question_difficulty="BASIC",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built REST APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI"],
        questions_asked=[],
    )
    assert res.accepted is False


def test_16_jd_gap_accepted_only_when_policy_permits():
    res = QuestionRelevanceService.validate_question(
        question_text="What is Kubernetes and what container problem does it solve?",
        question_difficulty="BASIC",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built REST APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI", "Kubernetes"],
        questions_asked=[],
    )
    assert res.accepted is True
    assert res.skill_tier == "JD_GAP"


def test_17_jd_gap_still_respects_difficulty_ceiling():
    res = QuestionRelevanceService.validate_question(
        question_text="How do you design a multi-region failover cluster in Kubernetes?",
        question_difficulty="ADVANCED",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built REST APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI", "Kubernetes"],
        questions_asked=[],
    )
    assert res.accepted is False
    assert res.difficulty_allowed is False


def test_18_paraphrased_duplicate_question_rejected():
    existing = [{"question_text": "What is dependency injection in FastAPI?"}]
    res = QuestionRelevanceService.validate_question(
        question_text="What is dependency injection in FastAPI?",
        question_difficulty="BASIC",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built REST APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI"],
        questions_asked=existing,
    )
    assert res.accepted is False
    assert res.duplicate_score > 0.35


def test_19_valid_novel_question_accepted():
    existing = [{"question_text": "What is dependency injection in FastAPI?"}]
    res = QuestionRelevanceService.validate_question(
        question_text="How does Pydantic perform data validation in FastAPI routes?",
        question_difficulty="BASIC",
        relevant_experience_months=2,
        seniority_level="JUNIOR",
        candidate_skills=["Python", "FastAPI"],
        work_experience_bullets=["Built REST APIs using FastAPI."],
        jd_required_skills=["Python", "FastAPI"],
        questions_asked=existing,
    )
    assert res.accepted is True


def test_20_deterministic_repeated_execution():
    runs = [
        QuestionRelevanceService.validate_question(
            question_text="How do path parameters work in FastAPI?",
            question_difficulty="BASIC",
            relevant_experience_months=2,
            seniority_level="JUNIOR",
            candidate_skills=["Python", "FastAPI"],
            work_experience_bullets=["Built REST APIs using FastAPI."],
            jd_required_skills=["Python", "FastAPI"],
            questions_asked=[],
        )
        for _ in range(5)
    ]
    first = runs[0].accepted
    for r in runs[1:]:
        assert r.accepted == first
