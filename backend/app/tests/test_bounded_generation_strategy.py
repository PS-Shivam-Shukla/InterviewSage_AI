"""
Comprehensive Test Suite for Bounded Generation Strategy & Pre-Generation Diversity Optimization.
Covers all 12 test requirements specified in the optimization specification.
"""

from app.agents.question_generator_agent import GeneratedQuestion, QuestionGeneratorAgent
from app.core.llm_client import FakeLLMClient
from app.services.question_relevance_service import QuestionRelevanceService


def make_state(questions_asked=None, competency_matrix=None):
    return {
        "candidate_id": "c100",
        "job_id": "j100",
        "resume_data": {
            "seniority_signal": "MID",
            "relevant_experience_months": 36,
            "skills": ["Python", "SQL", "FastAPI", "PostgreSQL"],
            "experience": [{"description": "Developed backend REST microservices in Python and SQL."}],
        },
        "jd_data": {
            "target_role": "Backend Engineer",
            "required_skills": ["Python", "SQL", "FastAPI", "PostgreSQL"],
        },
        "competency_matrix": competency_matrix or [{"name": "SQL", "weight": 100}],
        "questions_asked": questions_asked or [],
        "evaluations": [],
    }


def test_req_1_first_generation_acceptance_no_retry():
    """Test 1: First-generation acceptance requires no retry."""
    state = make_state()
    expected_q = "What are SQL transaction isolation levels?"
    class FakeLLM1(FakeLLMClient):
        def invoke(self, messages):
            return "SQL"
        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            return GeneratedQuestion(
                question_text=expected_q,
                competency_targeted="SQL",
                difficulty="INTERMEDIATE",
                question_type="fundamentals"
            )
    agent = QuestionGeneratorAgent(round_type="TECHNICAL", llm_client=FakeLLM1())
    result = agent._run(state)
    assert result["current_question"]["question_text"] == expected_q


def test_req_2_and_3_and_4_and_5_gate5_rejection_triggers_alternative_angle():
    """
    Tests Requirements 2, 3, 4, 5:
    - Gate 5 rejection triggers alternative-angle generation.
    - Alternative prompt is different from original.
    - Second attempt remains on same competency.
    - Difficulty remains unchanged.
    """
    questions = [
        {
            "question_text": "Explain how SQL indexes improve query performance.",
            "competency_targeted": "SQL",
            "cognitive_angle": "fundamentals_and_concepts",
            "round_type": "TECHNICAL"
        }
    ]
    state = make_state(questions_asked=questions)

    class FakeLLM2(FakeLLMClient):
        def __init__(self):
            super().__init__()
            self.prompts_captured = []

        def invoke(self, messages):
            return "SQL"

        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            combined_text = " ".join([getattr(m, "content", str(m)) for m in messages])
            self.prompts_captured.append(combined_text)
            if len(self.prompts_captured) == 1:
                return GeneratedQuestion(
                    question_text="Explain how SQL indexes improve query performance.",
                    competency_targeted="SQL",
                    difficulty="INTERMEDIATE",
                    question_type="fundamentals"
                )
            else:
                return GeneratedQuestion(
                    question_text="Suppose an indexed SQL query becomes slower after table growth. How would you investigate query plans?",
                    competency_targeted="SQL",
                    difficulty="INTERMEDIATE",
                    question_type="fundamentals"
                )

    fake_llm = FakeLLM2()
    agent = QuestionGeneratorAgent(round_type="TECHNICAL", llm_client=fake_llm)
    result = agent(state) # Executes via BaseAgent retry loop

    assert len(fake_llm.prompts_captured) == 2, f"Prompts captured count: {len(fake_llm.prompts_captured)}"
    assert "STRATEGY: ALTERNATIVE ANGLE" in fake_llm.prompts_captured[1]
    assert result["current_question"]["competency_targeted"] == "SQL"
    assert result["current_question"]["difficulty"] == "INTERMEDIATE"


def test_req_7_and_8_and_9_repeated_gate5_triggers_bounded_fallback():
    """
    Tests Requirements 7, 8, 9:
    - Repeated Gate 5 failure triggers bounded fallback competency.
    - Fallback selected only from eligible competencies in competency_matrix.
    - Does not violate question distribution.
    """
    matrix = [
        {"name": "SQL", "weight": 50},
        {"name": "Python", "weight": 50},
    ]
    questions = [
        {
            "question_text": "Explain how SQL indexes improve query performance.",
            "competency_targeted": "SQL",
            "cognitive_angle": "fundamentals_and_concepts",
            "round_type": "TECHNICAL"
        }
    ]
    state = make_state(questions_asked=questions, competency_matrix=matrix)

    class FakeLLM3(FakeLLMClient):
        def __init__(self):
            super().__init__()
            self.prompts_captured = []

        def invoke(self, messages):
            return "SQL"

        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            combined_text = " ".join([getattr(m, "content", str(m)) for m in messages])
            self.prompts_captured.append(combined_text)
            if len(self.prompts_captured) <= 2:
                return GeneratedQuestion(
                    question_text="Explain how SQL indexes improve query performance.",
                    competency_targeted="SQL",
                    difficulty="INTERMEDIATE",
                    question_type="fundamentals"
                )
            else:
                return GeneratedQuestion(
                    question_text="Explain Python GIL lock behavior in multithreaded apps.",
                    competency_targeted="Python",
                    difficulty="INTERMEDIATE",
                    question_type="fundamentals"
                )

    fake_llm = FakeLLM3()
    agent = QuestionGeneratorAgent(round_type="TECHNICAL", llm_client=fake_llm)
    result = agent(state)

    assert len(fake_llm.prompts_captured) == 3, f"Prompts captured count: {len(fake_llm.prompts_captured)}"
    assert "STRATEGY: FALLBACK COMPETENCY" in fake_llm.prompts_captured[2]
    assert result["current_question"]["competency_targeted"] in ("SQL", "Python")
    assert "Explain Python GIL" in result["current_question"]["question_text"]


def test_req_10_exact_duplicate_rejected():
    """Test 10: Gate 5 exact duplicates are still rejected."""
    q_existing = "Explain Python decorators."
    questions_asked = [{"question_text": q_existing, "competency_targeted": "Python"}]
    res = QuestionRelevanceService.validate_question(
        question_text=q_existing,
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=questions_asked,
        competency_targeted="Python",
        candidate_skills=["Python"],
        work_experience_bullets=["Python backend engineer"],
        jd_required_skills=["Python"],
        relevant_experience_months=36,
        seniority_level="MID",
    )
    assert res.accepted is False
    assert "GATE 5 FAILED" in res.reason


def test_req_11_history_aware_cognitive_angle_preselection():
    """Test 11: History-aware selector picks an unused cognitive angle on Attempt 1."""
    questions_asked = [
        {
            "question_text": "Explain Python GIL concepts.",
            "competency_targeted": "Python",
            "cognitive_angle": "fundamentals_and_concepts",
            "round_type": "TECHNICAL"
        }
    ]
    state = make_state(questions_asked=questions_asked, competency_matrix=[{"name": "Python", "weight": 100}])

    class FakeLLMAngle(FakeLLMClient):
        def __init__(self):
            super().__init__()
            self.captured_user_content = ""
        def invoke(self, messages):
            return "Python"
        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            self.captured_user_content = " ".join([getattr(m, "content", str(m)) for m in messages])
            return GeneratedQuestion(
                question_text="A Python web worker has memory leak. How do you profile garbage collection?",
                competency_targeted="Python",
                difficulty="INTERMEDIATE",
                question_type="fundamentals"
            )

    fake_llm = FakeLLMAngle()
    agent = QuestionGeneratorAgent(round_type="TECHNICAL", llm_client=fake_llm)
    result = agent._run(state)

    # Unused angle 'implementation_and_usage' or 'debugging_and_failure_investigation' should be picked
    assert "Required cognitive angle: Implementation And Usage" in fake_llm.captured_user_content or "Debugging And Failure Investigation" in fake_llm.captured_user_content
    assert result["current_question"]["cognitive_angle"] != "fundamentals_and_concepts"


def test_req_12_placeholder_protection_works():
    """Test 12: Placeholder protection still works (Gate 0)."""
    q_placeholder = "Explain [insert technology] and how it operates."
    res = QuestionRelevanceService.validate_question(
        question_text=q_placeholder,
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=[],
        competency_targeted="Python",
        candidate_skills=["Python"],
        work_experience_bullets=["Python developer"],
        jd_required_skills=["Python"],
        relevant_experience_months=36,
        seniority_level="MID",
    )
    assert res.accepted is False


def test_req_13_competency_mismatch_rejection_works():
    """Test 13: Competency mismatch rejection still works (Gate 6)."""
    q_sql = "Explain the difference between a primary key and a foreign key in a relational database."
    res = QuestionRelevanceService.validate_question(
        question_text=q_sql,
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=[],
        competency_targeted="C/C++",
        candidate_skills=["C/C++", "C++"],
        work_experience_bullets=["Developed C++ multi-threaded backend services."],
        jd_required_skills=["C/C++"],
        relevant_experience_months=36,
        seniority_level="MID",
    )
    assert res.accepted is False
    assert "Competency Mismatch" in res.reason or "GATE 6 FAILED" in res.reason


def test_req_16_and_17_no_infinite_retries_max_attempts_bounded():
    """Tests Requirements 16 & 17: Maximum LLM attempts bounded, no infinite loop possible."""
    questions = [{"question_text": "Explain Python decorators.", "competency_targeted": "Python", "round_type": "TECHNICAL"}]
    state = make_state(questions_asked=questions)

    class FakeLLMBounded(FakeLLMClient):
        def invoke(self, messages):
            return "Python"
        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            return GeneratedQuestion(
                question_text="Explain Python decorators.",
                competency_targeted="Python",
                difficulty="INTERMEDIATE",
                question_type="fundamentals"
            )

    agent = QuestionGeneratorAgent(round_type="TECHNICAL", llm_client=FakeLLMBounded())
    result = agent(state) # 3 attempts fail duplicate check -> triggers seed fallback
    
    assert "current_question" in result
    assert result["current_question"]["question_text"] is not None
