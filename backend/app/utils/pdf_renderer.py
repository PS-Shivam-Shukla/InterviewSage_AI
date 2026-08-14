"""PDF rendering utilities using ReportLab."""

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render_report_pdf(report_data: dict[str, Any]) -> bytes:
    """Render a nicely formatted PDF for the interview report.

    Includes candidate skill competency matrix, overall score, question transcript,
    and detailed per-question AI feedback.
    Returns PDF bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
    )
    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8,
    )
    normal = ParagraphStyle(
        "BodyNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
    )
    small = ParagraphStyle(
        "BodySmall",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )
    question_style = ParagraphStyle(
        "QuestionText",
        parent=normal,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e40af"),
        fontName="Helvetica-Bold",
    )
    feedback_style = ParagraphStyle(
        "FeedbackText",
        parent=normal,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#065f46"),
        fontName="Helvetica-Oblique",
    )

    # ── 1. Document Header ───────────────────────────────────────────────────
    role = report_data.get("role") or "Software Engineering Candidate"
    interview_id = report_data.get("interview_id", "N/A")
    gen_at = report_data.get("generated_at", "")
    overall_score = report_data.get("overall_score")

    story.append(Paragraph("AI Interview Evaluation Report", title_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(f"<b>Target Role:</b> {role} | <b>Session ID:</b> {interview_id}", subtitle_style)
    )
    if gen_at:
        story.append(Paragraph(f"<b>Generated At:</b> {gen_at}", small))
    if overall_score is not None:
        score_num = float(overall_score)
        story.append(Spacer(1, 6))
        story.append(
            Paragraph(
                f"<b>Overall Scorecard Rating:</b> {score_num:.1f}%",
                ParagraphStyle(
                    "OverallBadge",
                    parent=normal,
                    fontSize=12,
                    leading=16,
                    textColor=colors.HexColor("#4338ca"),
                    fontName="Helvetica-Bold",
                ),
            )
        )
    story.append(Spacer(1, 12))

    # ── 2. Competency & Skill Scorecard ──────────────────────────────────────
    story.append(Paragraph("Candidate Skill & Competency Scorecard", h2_style))
    scorecard = report_data.get("competency_scorecard") or []

    if scorecard:
        rows = [["Skill / Competency Target", "Score (%)", "Proficiency Level"]]
        for item in scorecard:
            if isinstance(item, dict):
                skill_name = (
                    item.get("competency") or item.get("skill") or item.get("name") or "Skill"
                )
                raw_score = item.get("score")
                if raw_score is not None:
                    sc_val = float(raw_score)
                    score_str = f"{sc_val:.1f}%"
                    if sc_val >= 80:
                        rating = "Advanced / Mastered"
                    elif sc_val >= 60:
                        rating = "Proficient / Competent"
                    else:
                        rating = "Needs Development"
                else:
                    score_str = "N/A"
                    rating = "Unevaluated"
                rows.append([skill_name, score_str, rating])
            else:
                rows.append([str(item), "N/A", "Unevaluated"])

        tbl = Table(rows, colWidths=[240, 100, 160])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ]
            )
        )
        story.append(tbl)
    else:
        story.append(Paragraph("No competency data recorded.", normal))
    story.append(Spacer(1, 14))

    # ── 3. Improvement Plan ──────────────────────────────────────────────────
    story.append(Paragraph("Targeted Improvement Plan", h2_style))
    plan = report_data.get("improvement_plan") or []
    if plan:
        for item in plan:
            if isinstance(item, dict):
                topic = (
                    item.get("topic")
                    or item.get("area")
                    or item.get("targetSkill")
                    or "Improvement Area"
                )
                desc = item.get("description") or item.get("recommendation") or ""
                priority = item.get("priority") or "Medium"
                story.append(Paragraph(f"• <b>{topic}</b> [{priority} Priority]: {desc}", normal))
            else:
                story.append(Paragraph(f"• {item}", normal))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No specific improvement areas flagged.", normal))
    story.append(Spacer(1, 14))

    # ── 4. Detailed Question Transcript & AI Feedback ────────────────────────
    story.append(Paragraph("Question Transcript & AI Evaluation Feedback", h2_style))
    transcript = report_data.get("transcript_snapshot") or []

    if transcript:
        for idx, qa in enumerate(transcript, start=1):
            if isinstance(qa, dict):
                q = qa.get("question") or "Question"
                a = qa.get("answer") or "No answer provided."
                score = qa.get("score")
                comp = qa.get("competency") or "General"
                reasoning = (
                    qa.get("reasoning") or qa.get("feedback") or "Evaluated via EvaluationAgent."
                )
                disp_score = qa.get("display_score") or (
                    f"{score:.1f}%" if score is not None else "N/A"
                )
            else:
                q = str(qa)
                a = ""
                disp_score = "N/A"
                comp = "General"
                reasoning = "N/A"

            story.append(Paragraph(f"Q{idx}. [{comp}] {q}", question_style))
            story.append(Spacer(1, 2))
            story.append(Paragraph(f"<b>Candidate Answer:</b> {a}", normal))
            story.append(Spacer(1, 2))
            story.append(Paragraph(f"<b>Score:</b> {disp_score}", small))
            story.append(Spacer(1, 2))
            story.append(
                Paragraph(f"<b>AI Feedback & Diagnostic Reasoning:</b> {reasoning}", feedback_style)
            )
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("No interview transcript available.", normal))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
