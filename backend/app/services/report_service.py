"""
Report generation service implementation.
100% Stateless — Reads session state directly from PostgreSQL database (Sprint 5).
"""

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import InterviewQuestion, InterviewReport, JobDescription
from app.repositories import (
    InterviewAnswerRepository,
    InterviewReportRepository,
    InterviewRepository,
)

logger = get_logger(__name__)


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.report_repo = InterviewReportRepository(db)
        self.answer_repo = InterviewAnswerRepository(db)
        self.interview_repo = InterviewRepository(db)

    def get_report(self, interview_id: str) -> dict | None:
        report = self.report_repo.get_by_interview(interview_id)
        if not report:
            db_answers = self.answer_repo.list_answers_with_evaluations_by_interview(interview_id)
            db_questions = self.db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview_id).all()
            if not db_answers and not db_questions:
                return None
            return self.generate_report(interview_id)

        role_title = self._resolve_role(interview_id)
        interview_obj = self.interview_repo.get_by_id(interview_id)

        return {
            "interview_id": report.interview_id,
            "status": interview_obj.status if interview_obj else "COMPLETED",
            "overall_score": float(interview_obj.overall_score) if interview_obj and interview_obj.overall_score is not None else 0.0,
            "role": role_title,
            "competency_scorecard": json.loads(report.competency_scorecard),
            "improvement_plan": json.loads(report.improvement_plan),
            "transcript_snapshot": json.loads(report.transcript_snapshot),
            "generated_at": report.generated_at,
        }

    def get_user_report_history(self, user_id: str) -> list[dict]:
        """
        Retrieve lightweight history of completed interview reports belonging to a specific user,
        ordered newest first.
        """
        from app.models import Interview
        interviews = (
            self.db.query(Interview)
            .filter(Interview.user_id == user_id, Interview.status == "COMPLETED")
            .order_by(Interview.created_at.desc())
            .all()
        )

        history = []
        for iv in interviews:
            rep = self.report_repo.get_by_interview(iv.id)
            role_title = self._resolve_role(iv.id)

            total_q = self.db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == iv.id).count()

            gen_time = rep.generated_at if rep else (iv.completed_at or iv.created_at)
            history.append({
                "interview_id": iv.id,
                "role": role_title,
                "status": iv.status,
                "overall_score": float(iv.overall_score) if iv.overall_score is not None else 0.0,
                "generated_at": gen_time,
                "completed_at": iv.completed_at,
                "total_questions": total_q or 0,
            })

        return history

    def get_report_pdf(self, interview_id: str) -> bytes | None:
        report_data = self.get_report(interview_id)
        if not report_data:
            return None
        return self._create_pdf(report_data)

    def _create_pdf(self, report_data: dict) -> bytes:
        """Create a formatted PDF document from report content using ReportLab."""
        try:
            from app.utils.pdf_renderer import render_report_pdf
            pdf_bytes = render_report_pdf(report_data)
            return pdf_bytes
        except Exception as exc:
            logger.warning(f"ReportLab PDF rendering fallback triggered for report {report_data.get('interview_id')}: {exc}")
            lines = [
                f"Interview Report: {report_data.get('interview_id')}",
                f"Generated At: {report_data.get('generated_at')}",
                "",
                "Transcript Snapshot:",
            ]
            for item in report_data.get("transcript_snapshot", []):
                lines.append(f"- Q: {item.get('question')} | A: {item.get('answer')} | Score: {item.get('score')}")

            escaped_lines = [self._escape_pdf_text(str(line)) for line in lines]
            stream_lines = [
                "BT",
                "/F1 12 Tf",
                "72 760 Td",
            ]
            for line in escaped_lines:
                stream_lines.append(f"({line}) Tj")
                stream_lines.append("0 -16 Td")
            stream_lines.append("ET")
            stream_data = "\n".join(stream_lines).encode("latin-1")

            objects = [
                b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
                b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
                b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
                b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
                f"5 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("latin-1")
                + stream_data
                + b"\nendstream\nendobj\n",
            ]

            pdf = bytearray(b"%PDF-1.4\n")
            offsets = []
            for obj in objects:
                offsets.append(len(pdf))
                pdf.extend(obj)

            xref_offset = len(pdf)
            pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
            pdf.extend(b"0000000000 65535 f \n")
            for offset in offsets:
                pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

            pdf.extend(
                f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1")
            )
            return bytes(pdf)

    def _resolve_role(self, interview_id: str) -> str:
        """Resolve the role title from the interview's JD. Never hardcodes a default role name."""
        interview_obj = self.interview_repo.get_by_id(interview_id)
        if interview_obj:
            if interview_obj.target_role:
                return interview_obj.target_role
            if interview_obj.jd_id:
                jd_obj = self.db.query(JobDescription).filter(
                    JobDescription.id == interview_obj.jd_id
                ).first()
                if jd_obj and jd_obj.target_role:
                    return jd_obj.target_role
        return "Interview"

    def generate_report(self, interview_id: str) -> dict:
        """
        Synthesize report from persisted evaluations in PostgreSQL.

        Competency scorecard: derived from actual InterviewQuestion.competency_targeted
        grouped against their Evaluation.score values.
        No hardcoded competency names. No fallback score of 85.
        """
        existing = self.report_repo.get_by_interview(interview_id)
        if existing:
            return {
                "interview_id": existing.interview_id,
                "competency_scorecard": json.loads(existing.competency_scorecard),
                "improvement_plan": json.loads(existing.improvement_plan),
                "transcript_snapshot": json.loads(existing.transcript_snapshot),
                "generated_at": existing.generated_at.isoformat() if hasattr(existing.generated_at, "isoformat") else str(existing.generated_at),
            }

        # ── Role title from JD ─────────────────────────────────────────────
        role_title = self._resolve_role(interview_id)
        interview_obj = self.interview_repo.get_by_id(interview_id)

        # ── Load all answers with evaluations ─────────────────────────────
        db_answers = self.answer_repo.list_answers_with_evaluations_by_interview(interview_id)

        # ── Load questions (for competency_targeted) ───────────────────────
        db_questions = (
            self.db.query(InterviewQuestion)
            .filter(InterviewQuestion.interview_id == interview_id)
            .order_by(InterviewQuestion.sequence_number)
            .all()
        )
        question_competency_map = {
            q.question_text.strip(): q.competency_targeted for q in db_questions
        }

        # ── Build transcript and collect per-competency scores ─────────────
        transcript = []
        # Maps: competency_name → list of 0-100 scores
        competency_scores: dict = {}
        all_scores: list = []

        for item in db_answers:
            eval_d = item.get("evaluation", {})
            score = eval_d.get("score") if isinstance(eval_d, dict) else None

            # Skip items with no real evaluation
            if score is None:
                continue

            score = float(score)
            all_scores.append(score)

            # Get competency from eval_result dict (stored by new interview_service)
            # or fall back to question_competency_map
            q_text = item.get("question_text", "")
            competency = (
                eval_d.get("competency_targeted")
                or question_competency_map.get(q_text.strip(), "")
                or "General"
            )

            if competency and competency != "General":
                competency_scores.setdefault(competency, []).append(score)

            raw_10 = eval_d.get("score_1_10") if isinstance(eval_d, dict) and "score_1_10" in eval_d else int(score / 10)
            disp_str = f"{raw_10}/10 ({int(score)}%)"

            transcript.append({
                "question": q_text or "Technical Question",
                "answer": item.get("candidate_answer", ""),
                "score": score,
                "score_1_10": raw_10,
                "display_score": disp_str,
                "competency": competency,
                "reasoning": eval_d.get("reasoning") or eval_d.get("feedback") or "Evaluated via EvaluationAgent",
                "feedback": eval_d.get("feedback") or eval_d.get("reasoning") or "Evaluated via EvaluationAgent",
            })

        # ── Overall score from persisted evaluations ───────────────────────
        overall = round(sum(all_scores) / max(1, len(all_scores)), 1) if all_scores else 0.0

        # ── Build competency scorecard from REAL per-question evaluations ──
        competency_scorecard = []
        for comp, scores in competency_scores.items():
            avg = round(sum(scores) / len(scores), 1)
            competency_scorecard.append({
                "competency": comp,
                "skill": comp,
                "name": comp,
                "score": avg,
                "fullMark": 100,
            })

        # Sort: highest-scoring competencies first
        competency_scorecard.sort(key=lambda x: x["score"], reverse=True)

        # If no evaluated answers had competency data, return empty rather than fake names
        if not competency_scorecard and db_questions:
            # Last resort: use question competencies with overall score
            seen_comps: set = set()
            for q in db_questions:
                comp_name = q.competency_targeted
                if comp_name and comp_name not in seen_comps:
                    seen_comps.add(comp_name)
                    competency_scorecard.append({
                        "competency": comp_name,
                        "skill": comp_name,
                        "name": comp_name,
                        "score": overall,
                        "fullMark": 100,
                    })

        # ── Build improvement plan from weak competencies ───────────────────
        improvement_plan = []
        weak_comps = [
            entry for entry in competency_scorecard if entry["score"] < 65
        ]
        if not weak_comps:
            # No weak areas: suggest advancement in top competency
            top_comp = competency_scorecard[0]["competency"] if competency_scorecard else role_title
            improvement_plan.append({
                "id": "imp-1",
                "topic": f"Advanced {top_comp} Mastery",
                "description": f"Deepen expertise in {top_comp} to reach senior-level proficiency for {role_title}.",
                "targetSkill": top_comp,
                "priority": "Medium",
            })
        else:
            for i, entry in enumerate(weak_comps[:3], start=1):
                comp = entry["competency"]
                improvement_plan.append({
                    "id": f"imp-{i}",
                    "topic": f"Strengthen {comp}",
                    "description": f"Score {entry['score']:.0f}% in {comp}. Focus on practical application and depth for {role_title} interviews.",
                    "targetSkill": comp,
                    "priority": "High" if entry["score"] < 50 else "Medium",
                })

        if not improvement_plan:
            improvement_plan.append({
                "id": "imp-1",
                "topic": f"{role_title} Best Practices",
                "description": f"Continue practising {role_title} interview scenarios and system design.",
                "targetSkill": role_title,
                "priority": "Low",
            })

        # ── Persist report ─────────────────────────────────────────────────
        report_obj = InterviewReport(
            interview_id=interview_id,
            competency_scorecard=json.dumps(competency_scorecard),
            improvement_plan=json.dumps(improvement_plan),
            transcript_snapshot=json.dumps(transcript),
            generated_at=datetime.now(UTC),
        )

        try:
            created = self.report_repo.create(report_obj)
            res_id = created.interview_id
        except Exception as exc:
            logger.error(f"Failed to persist report for {interview_id}: {exc}", exc_info=True)
            res_id = interview_id

        if interview_obj and interview_obj.overall_score is None and all_scores:
            try:
                from app.repositories import InterviewRepository as IR
                IR(self.db).update(interview_id, {"overall_score": int(round(overall))})
                self.db.commit()
            except Exception:
                pass

        return {
            "interview_id": res_id,
            "role": role_title,
            "overall_score": overall,
            "competency_scorecard": competency_scorecard,
            "improvement_plan": improvement_plan,
            "transcript_snapshot": transcript,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def _escape_pdf_text(self, text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
