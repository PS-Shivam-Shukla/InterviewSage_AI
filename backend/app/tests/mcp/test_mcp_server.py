"""
MCP Server and tool unit tests.
"""

import pytest

from app.mcp.server import MCPServer, _match_uri
from app.mcp.tools.compute_ats_score import compute_ats_score
from app.mcp.tools.fetch_industry_standards import fetch_industry_standards
from app.mcp.tools.generate_report_pdf import generate_report_pdf
from app.mcp.tools.parse_jd import parse_jd_text
from app.mcp.tools.score_answer_rubric import score_answer_rubric

# ─────────────────────────────────────────────────────────────
# MCPServer core
# ─────────────────────────────────────────────────────────────

class TestMCPServerRegistry:
    def _server(self) -> MCPServer:
        s = MCPServer()
        s.register_tool(
            name="echo",
            description="Echo back input",
            parameters={"msg": {"type": "string"}},
            handler=lambda msg: msg,
            required_params=["msg"],
        )
        return s

    def test_list_tools(self):
        s = self._server()
        tools = s.list_tools()
        assert any(t["name"] == "echo" for t in tools)

    def test_call_tool_success(self):
        s = self._server()
        result = s.call_tool("echo", msg="hello")
        assert result.success is True
        assert result.output == "hello"

    def test_call_tool_missing_required(self):
        s = self._server()
        result = s.call_tool("echo")       # missing msg
        assert result.success is False
        assert "Missing required" in (result.error or "")

    def test_call_unknown_tool(self):
        s = self._server()
        result = s.call_tool("nonexistent")
        assert result.success is False
        assert "Unknown tool" in (result.error or "")

    def test_call_log_appended(self):
        s = self._server()
        s.call_tool("echo", msg="test")
        assert len(s.get_call_log()) == 1
        assert s.get_call_log()[0]["tool"] == "echo"

    def test_reset_call_log(self):
        s = self._server()
        s.call_tool("echo", msg="x")
        s.reset_call_log()
        assert s.get_call_log() == []

    def test_tool_error_captured(self):
        s = MCPServer()
        s.register_tool("boom", "raises", {}, lambda: 1 / 0)
        result = s.call_tool("boom")
        assert result.success is False
        assert result.error is not None

    def test_resource_registration_and_read(self):
        s = MCPServer()
        s.register_resource(
            uri_template="resource://test/{key}",
            description="test resource",
            handler=lambda key: {"value": key},
        )
        out = s.read_resource("resource://test/hello")
        assert out == {"value": "hello"}

    def test_resource_not_found(self):
        s = MCPServer()
        out = s.read_resource("resource://nothing/here")
        assert out is None

    def test_prompt_registry(self):
        s = MCPServer()
        s.register_prompt("test_prompt", "v1", "Hello {name}!")
        tpl = s.get_prompt("test_prompt", "v1")
        assert tpl == "Hello {name}!"

    def test_prompt_missing_version(self):
        s = MCPServer()
        tpl = s.get_prompt("nonexistent", "v1")
        assert tpl is None


class TestURIMatching:
    def test_exact_match(self):
        assert _match_uri("resource://a/b", "resource://a/b") == {}

    def test_single_variable(self):
        result = _match_uri("resource://standards/{role}", "resource://standards/backend")
        assert result == {"role": "backend"}

    def test_multi_variable(self):
        result = _match_uri("resource://bank/{role}/{level}", "resource://bank/frontend/HARD")
        assert result == {"role": "frontend", "level": "HARD"}

    def test_no_match_different_length(self):
        assert _match_uri("resource://a/b", "resource://a/b/c") is None

    def test_no_match_literal_mismatch(self):
        assert _match_uri("resource://a/b", "resource://a/x") is None


# ─────────────────────────────────────────────────────────────
# Individual tool tests
# ─────────────────────────────────────────────────────────────

class TestComputeATSScore:
    def test_full_match(self):
        result = compute_ats_score(["Python", "FastAPI"], ["Python", "FastAPI"])
        assert result["overlap_score"] == 100
        assert result["missing_keywords"] == []

    def test_partial_match(self):
        result = compute_ats_score(["Python"], ["Python", "FastAPI", "PostgreSQL"])
        assert result["overlap_score"] < 100
        assert "fastapi" in result["missing_keywords"]
        assert "postgresql" in result["missing_keywords"]

    def test_zero_match(self):
        result = compute_ats_score(["Java"], ["Python", "FastAPI"])
        assert result["overlap_score"] == 0
        assert len(result["missing_keywords"]) == 2

    def test_empty_jd_skills(self):
        result = compute_ats_score(["Python"], [])
        assert result["overlap_score"] == 0
        assert result["jd_skill_count"] == 0

    def test_case_insensitive(self):
        result = compute_ats_score(["PYTHON", "fastapi"], ["python", "FastAPI"])
        assert result["overlap_score"] == 100


class TestFetchIndustryStandards:
    def test_known_role(self):
        result = fetch_industry_standards("backend-engineer")
        assert "core_skills" in result
        assert "key_competencies" in result
        assert len(result["key_competencies"]) > 0

    def test_normalisation(self):
        result = fetch_industry_standards("Backend Engineer")
        assert "core_skills" in result

    def test_unknown_role_returns_default(self):
        result = fetch_industry_standards("quantum-shaman")
        assert "key_competencies" in result

    def test_competency_weights_present(self):
        result = fetch_industry_standards("frontend-engineer")
        total = sum(c["weight"] for c in result["key_competencies"])
        assert total == 100


class TestParseJDText:
    def test_basic(self):
        result = parse_jd_text("We need a Python developer with 5 years experience.")
        assert result["word_count"] > 0
        assert "normalized_text" in result

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_jd_text("")

    def test_detects_requirements_section(self):
        text = "Requirements: Python, SQL, Docker"
        result = parse_jd_text(text)
        assert result["has_requirements_section"] is True

    def test_detects_responsibilities_section(self):
        text = "Responsibilities: Build APIs. Deploy services."
        result = parse_jd_text(text)
        assert result["has_responsibilities_section"] is True


class TestScoreAnswerRubric:
    def test_behavioral(self):
        rubric = score_answer_rubric("behavioral")
        assert len(rubric["dimensions"]) == 5
        total_weight = sum(d["weight"] for d in rubric["dimensions"])
        assert total_weight == 100

    def test_system_design(self):
        rubric = score_answer_rubric("system_design")
        assert len(rubric["dimensions"]) == 6

    def test_alias_hr(self):
        rubric = score_answer_rubric("hr")
        assert len(rubric["dimensions"]) == 5   # maps to behavioral

    def test_unknown_type_defaults_to_fundamentals(self):
        rubric = score_answer_rubric("random_type")
        assert "dimensions" in rubric

    def test_seniority_context_present(self):
        rubric = score_answer_rubric("fundamentals", "SENIOR")
        assert "strict" in rubric["seniority_context"].lower()


class TestGenerateReportPDF:
    def test_creates_file(self, tmp_path):
        report_data = {
            "interview_id": "test-123",
            "overall_score": 8,
            "competency_scorecard": [{"competency": "Coding", "score": 8}],
            "improvement_plan": [
                {"competency": "System Design",
                 "recommended_action": "Study distributed systems"}
            ],
        }
        result = generate_report_pdf(report_data, output_dir=str(tmp_path))
        assert result["success"] is True
        from pathlib import Path
        assert Path(result["file_path"]).exists()

    def test_output_contains_interview_id(self, tmp_path):
        report_data = {
            "interview_id": "abc-456",
            "overall_score": 7,
            "competency_scorecard": [],
            "improvement_plan": [],
        }
        result = generate_report_pdf(report_data, output_dir=str(tmp_path))
        content = open(result["file_path"]).read()
        assert "abc-456" in content
