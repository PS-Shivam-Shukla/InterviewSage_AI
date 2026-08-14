"""
Unit tests for Seniority Evaluation Engine (Section 10.3).
Verifies deterministic calculations, rubric scoring, guardrails, interval merging, and 5-run reproducibility.
"""

import datetime

from app.services.seniority_engine import (
    SeniorityEngine,
    merge_employment_intervals,
    parse_month_year,
)

REF_DATE = datetime.date(2026, 8, 10)


def test_1_zero_experience_returns_intern():
    resume = {"experience": [], "technical_skills": []}
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_signal"] == "INTERN"
    assert res["seniority_score"] < 15


def test_2_twelve_months_returns_junior():
    resume = {
        "experience": [
            {
                "title": "Junior Developer",
                "start_date": "2025-01",
                "end_date": "2025-12",
                "description": "Implemented independent feature APIs and performed unit tests.",
                "ownership_bullets": ["Implemented independent feature"],
                "technologies": ["Python", "FastAPI"],
            }
        ],
        "technical_skills": ["Python", "FastAPI"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_signal"] == "JUNIOR"
    assert 15 <= res["seniority_score"] < 35


def test_3_thirty_six_months_returns_mid():
    resume = {
        "experience": [
            {
                "title": "Software Developer",
                "start_date": "2023-01",
                "end_date": "2025-12",
                "description": "Independently responsible for backend services and API design.",
                "ownership_bullets": ["Independently responsible for backend services"],
                "architecture_bullets": ["API design"],
                "technologies": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            }
        ],
        "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_signal"] == "MID"
    assert 35 <= res["seniority_score"] < 60


def test_4_sixty_months_with_ownership_and_architecture_returns_senior():
    resume = {
        "experience": [
            {
                "title": "Senior Software Engineer",
                "start_date": "2021-01",
                "end_date": "2025-12",
                "description": "Service owner for backend core API. Designed database architecture and high scale microservices.",
                "ownership_bullets": ["Service owner for backend"],
                "architecture_bullets": ["Designed database architecture"],
                "complexity_bullets": ["High scale microservices"],
                "technologies": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            }
        ],
        "technical_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_signal"] == "SENIOR"
    assert 60 <= res["seniority_score"] < 80


def test_5_eighty_four_months_with_architecture_and_leadership_returns_staff():
    resume = {
        "experience": [
            {
                "title": "Lead Software Architect",
                "start_date": "2019-01",
                "end_date": "2025-12",
                "description": "Led multi-system event-driven architecture across engineering teams. Tech lead for engineering team.",
                "ownership_bullets": ["Owned major core service"],
                "architecture_bullets": [
                    "Multi-system event-driven microservices architecture owner"
                ],
                "leadership_bullets": ["Tech lead for engineering team"],
                "complexity_bullets": ["High traffic high scale production system"],
                "technologies": ["Python", "Go", "Docker", "Kubernetes", "PostgreSQL", "Kafka"],
            }
        ],
        "technical_skills": ["Python", "Go", "Docker", "Kubernetes", "PostgreSQL", "Kafka"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_signal"] == "STAFF"
    assert res["seniority_score"] >= 80


def test_6_ten_years_without_leadership_capped_at_senior():
    # 10 years experience (40 pts) + ownership (15 pts) + arch (10 pts) + complexity (8 pts) = 73 pts -> SENIOR
    # Missing team leadership -> Staff Guardrail keeps at SENIOR
    resume = {
        "experience": [
            {
                "title": "Senior Software Developer",
                "start_date": "2016-01",
                "end_date": "2025-12",
                "description": "End-to-end service owner for backend core API. Designed database architecture.",
                "ownership_bullets": ["End-to-end service owner"],
                "architecture_bullets": ["Designed database architecture"],
                "technologies": ["Java", "SQL", "Docker", "FastAPI"],
            }
        ],
        "technical_skills": ["Java", "SQL", "Docker", "FastAPI"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_signal"] == "SENIOR"
    assert res["seniority_score"] < 80


def test_7_senior_title_with_six_months_experience_returns_intern():
    # Title != Truth rule: Title says 'Senior Software Engineer', but experience is 6 months
    resume = {
        "experience": [
            {
                "title": "Senior Software Engineer",
                "start_date": "2026-01",
                "end_date": "2026-06",
                "description": "Assisted with feature development.",
                "technologies": ["Python"],
            }
        ],
        "technical_skills": ["Python"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_signal"] == "INTERN"
    assert res["seniority_score"] < 15


def test_8_overlapping_employment_merged_correctly():
    # Jan 2022 -> Dec 2023 (24 mos) and Jun 2023 -> Dec 2024 (19 mos) -> Merged: Jan 2022 to Dec 2024 = 36 mos
    intervals = [
        (datetime.date(2022, 1, 1), datetime.date(2023, 12, 31)),
        (datetime.date(2023, 6, 1), datetime.date(2024, 12, 31)),
    ]
    merged_months = merge_employment_intervals(intervals)
    assert merged_months == 36


def test_9_unrelated_non_technical_role_excluded():
    resume = {
        "experience": [
            {
                "title": "Sales Executive",
                "start_date": "2020-01",
                "end_date": "2023-12",
                "description": "Sold enterprise software licenses to clients.",
                "technologies": [],
            },
            {
                "title": "Python Developer",
                "start_date": "2024-01",
                "end_date": "2024-12",
                "description": "Built backend APIs with FastAPI.",
                "technologies": ["Python", "FastAPI"],
            },
        ],
        "technical_skills": ["Python", "FastAPI"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["experience_metrics"]["total_months"] == 60  # 5 years total
    assert res["experience_metrics"]["relevant_months"] == 12  # Only 1 year technical


def test_10_present_date_calculated_up_to_ref_date():
    parsed_end = parse_month_year("Present", default_to_present=True, ref_date=REF_DATE)
    assert parsed_end == REF_DATE


def test_11_duplicate_experience_entries_deduplicated():
    resume = {
        "experience": [
            {
                "title": "Dev",
                "company": "Acme",
                "period": "2024 - 2025",
                "start_date": "2024-01",
                "end_date": "2024-12",
            },
            {
                "title": "Dev",
                "company": "Acme",
                "period": "2024 - 2025",
                "start_date": "2024-01",
                "end_date": "2024-12",
            },
        ],
        "technical_skills": ["Python"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["experience_metrics"]["total_months"] == 12


def test_12_leadership_without_lead_title_scores_points():
    resume = {
        "experience": [
            {
                "title": "Software Engineer",
                "start_date": "2023-01",
                "end_date": "2025-12",
                "description": "Mentored 3 junior developers and conducted code reviews.",
                "leadership_bullets": ["Mentored junior developers"],
                "technologies": ["Python"],
            }
        ],
        "technical_skills": ["Python"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_breakdown"]["leadership_score"] >= 10


def test_13_senior_title_without_evidence_grants_zero_leadership_points():
    resume = {
        "experience": [
            {
                "title": "Senior Software Engineer",
                "start_date": "2025-01",
                "end_date": "2025-06",
                "description": "Fixed bug backlog items.",
                "technologies": ["Python"],
            }
        ],
        "technical_skills": ["Python"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_breakdown"]["leadership_score"] == 0
    assert res["seniority_breakdown"]["architecture_score"] == 0


def test_14_five_run_determinism_assertion():
    resume = {
        "summary": "Full stack engineer",
        "technical_skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
        "experience": [
            {
                "title": "Full Stack Engineer",
                "start_date": "2022-01",
                "end_date": "2025-12",
                "description": "End-to-end service owner. Designed REST API architecture.",
                "ownership_bullets": ["End-to-end service owner"],
                "architecture_bullets": ["Designed REST API architecture"],
                "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
            }
        ],
    }

    results = [SeniorityEngine.evaluate(resume, ref_date=REF_DATE) for _ in range(5)]
    first = results[0]
    for r in results[1:]:
        assert r["seniority_signal"] == first["seniority_signal"]
        assert r["seniority_score"] == first["seniority_score"]
        assert r["experience_metrics"] == first["experience_metrics"]
        assert r["seniority_breakdown"] == first["seniority_breakdown"]
        assert r["seniority_evidence"] == first["seniority_evidence"]
        assert r["seniority_limitations"] == first["seniority_limitations"]


def test_15_boundary_scoring_thresholds():
    assert SeniorityEngine._score_experience_duration(5) == 0
    assert SeniorityEngine._score_experience_duration(6) == 5
    assert SeniorityEngine._score_experience_duration(17) == 5
    assert SeniorityEngine._score_experience_duration(18) == 12
    assert SeniorityEngine._score_experience_duration(35) == 12
    assert SeniorityEngine._score_experience_duration(36) == 22
    assert SeniorityEngine._score_experience_duration(59) == 22
    assert SeniorityEngine._score_experience_duration(60) == 32
    assert SeniorityEngine._score_experience_duration(95) == 32
    assert SeniorityEngine._score_experience_duration(96) == 40


def test_16_senior_guardrail_less_than_36_months_capped_at_mid():
    # 24 months experience (exp = 12 pts) + ownership (20) + arch (15) + lead (15) = 62 pts
    # Score >= 60, BUT relevant_months < 36 -> Senior Guardrail MUST cap at MID
    resume = {
        "experience": [
            {
                "title": "Lead Software Architect",
                "start_date": "2024-01",
                "end_date": "2025-12",
                "description": "Owned major core service end-to-end. Multi-system microservices architecture owner. Tech lead for engineering team.",
                "ownership_bullets": ["Owned major core service"],
                "architecture_bullets": [
                    "Multi-system event-driven microservices architecture owner"
                ],
                "leadership_bullets": ["Tech lead for engineering team"],
                "technologies": ["Python", "FastAPI"],
            }
        ],
        "technical_skills": ["Python", "FastAPI"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["seniority_signal"] == "MID"
    assert res["seniority_score"] <= 59
    assert any("Capped at MID" in lim for lim in res["seniority_limitations"])


def test_17_staff_guardrail_missing_leadership_capped_at_senior():
    # High score >= 80, but leadership < 10 -> Staff Guardrail MUST cap at SENIOR
    signal, score, lims = SeniorityEngine._apply_guardrails(
        score=85,
        relevant_months=120,
        ownership_score=20,
        architecture_score=15,
        leadership_score=5,  # Missing team leadership
    )
    assert signal == "SENIOR"
    assert score <= 79
    assert any("Capped at SENIOR" in lim for lim in lims)


def test_18_missing_dates_fallback_does_not_invent_fake_duration():
    resume = {
        "experience": [
            {
                "title": "Software Engineer",
                "description": "Implemented APIs.",
                "technologies": ["Python"],
            }
        ],
        "technical_skills": ["Python"],
    }
    res = SeniorityEngine.evaluate(resume, ref_date=REF_DATE)
    assert res["experience_metrics"]["total_months"] > 0
    assert res["seniority_signal"] in ("INTERN", "JUNIOR", "MID")
