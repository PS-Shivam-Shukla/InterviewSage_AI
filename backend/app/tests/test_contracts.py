from __future__ import annotations

from app.core.contracts import (
    ATSScoreContract,
    BlueprintConstraintContract,
    EvaluationConfidenceContract,
    NegativeConstraintContract,
)


def test_negative_constraint_contract():
    # Negative constraint passes when no forbidden keyword is present
    res1 = NegativeConstraintContract.validate(
        "Explain Python asyncio event loops and coroutine task scheduling.",
        ["React", "Vue", "Frontend"],
    )
    assert res1.is_valid is True
    assert len(res1.violations) == 0

    # Negative constraint fails when forbidden keyword 'React' is present
    res2 = NegativeConstraintContract.validate(
        "How do you build a React 19 component using hooks?", ["React", "Vue", "Frontend"]
    )
    assert res2.is_valid is False
    assert "React" in res2.violations


def test_blueprint_constraint_contract():
    valid_bp = {"total_questions": 2, "blueprint_items": [{"seq": 1}, {"seq": 2}]}
    assert BlueprintConstraintContract.validate(valid_bp).is_valid is True

    invalid_bp = {"total_questions": 5, "blueprint_items": [{"seq": 1}]}
    assert BlueprintConstraintContract.validate(invalid_bp).is_valid is False


def test_evaluation_confidence_contract():
    valid_eval = {"score": 85.0, "confidence_score": 0.90}
    assert EvaluationConfidenceContract.validate(valid_eval).is_valid is True

    low_conf_eval = {"score": 85.0, "confidence_score": 0.50}
    assert EvaluationConfidenceContract.validate(low_conf_eval).is_valid is False


def test_ats_score_contract():
    valid_ats = {"ats_score": 88}
    assert ATSScoreContract.validate(valid_ats).is_valid is True

    invalid_ats = {"ats_score": 150}
    assert ATSScoreContract.validate(invalid_ats).is_valid is False
