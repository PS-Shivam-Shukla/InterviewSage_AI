"""
MCP Tool: generate_report_pdf
Generates a PDF version of a completed interview report.
In v1 this uses a simple HTML-to-text fallback; a proper
weasyprint/reportlab renderer can be swapped in later.
"""

import json
from pathlib import Path
from typing import Any


def generate_report_pdf(
    report_data: dict[str, Any], output_dir: str = "./uploads"
) -> dict[str, Any]:
    """
    Generate a PDF report from interview report data.

    Args:
        report_data: The full InterviewReport dict.
        output_dir:  Directory to write the PDF into.

    Returns:
        {"file_path": str, "file_name": str, "success": bool}
    """
    interview_id = report_data.get("interview_id", "unknown")
    file_name = f"report_{interview_id}.txt"
    output_path = Path(output_dir) / file_name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Plain-text report (PDF renderer is a future enhancement)
    lines = [
        "=" * 60,
        "INTERVIEWSAGE AI — INTERVIEW REPORT",
        "=" * 60,
        f"Interview ID : {interview_id}",
        f"Overall Score: {report_data.get('overall_score', 'N/A')} / 10",
        "",
        "─── Competency Scorecard ───────────────────────────────",
    ]

    scorecard = report_data.get("competency_scorecard", [])
    if isinstance(scorecard, str):
        scorecard = json.loads(scorecard)
    for item in scorecard:
        lines.append(f"  {item.get('competency', '?'):<30} {item.get('score', '?')}/10")

    lines += [
        "",
        "─── Improvement Plan ───────────────────────────────────",
    ]
    plan = report_data.get("improvement_plan", [])
    if isinstance(plan, str):
        plan = json.loads(plan)
    for i, item in enumerate(plan, 1):
        lines.append(f"  {i}. [{item.get('competency', '?')}] {item.get('recommended_action', '')}")

    lines += ["", "=" * 60]

    output_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "file_path": str(output_path),
        "file_name": file_name,
        "success": True,
    }
