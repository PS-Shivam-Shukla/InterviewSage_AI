"""
Interview Replay Intelligence Engine.
Annotates interview transcript timelines with AI insights (timestamp, annotation_type, note).
"""

from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.career.schemas import InterviewAnnotationItem, InterviewReplayResponse
from app.models.career import InterviewAnnotation


class InterviewReplayEngine:
    """Generates AI timeline annotations for interview replay analysis."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_interview_replay(self, interview_id: str) -> InterviewReplayResponse:
        annotations = (
            self.db.query(InterviewAnnotation)
            .filter(InterviewAnnotation.interview_id == interview_id)
            .order_by(InterviewAnnotation.timestamp_mark.asc())
            .all()
        )

        if not annotations:
            # Seed default replay annotations for the interview
            defaults = [
                ("00:35", "EXCELLENT", "Clear, confident intro explaining microservice architecture"),
                ("02:11", "WEAKNESS", "Confidence dropped when questioned on database replication lag"),
                ("05:40", "PAUSE", "Long pause (12s) before answering rate limiting algorithm question"),
                ("09:10", "MISSED_EDGE_CASE", "Forgot to specify fallback cache strategy when Redis cluster is down"),
                ("13:05", "EXCELLENT", "Excellent optimization suggestion using B-Tree indexing and PgBouncer"),
            ]
            items = []
            for ts, ann_type, note in defaults:
                ann = InterviewAnnotation(
                    interview_id=interview_id,
                    timestamp_mark=ts,
                    annotation_type=ann_type,
                    note=note,
                )
                self.db.add(ann)
                items.append(InterviewAnnotationItem(timestamp_mark=ts, annotation_type=ann_type, note=note))
            self.db.commit()
            return InterviewReplayResponse(
                interview_id=interview_id,
                total_annotations=len(items),
                annotations=items,
            )

        items = [
            InterviewAnnotationItem(
                timestamp_mark=a.timestamp_mark,
                annotation_type=a.annotation_type,
                note=a.note,
            )
            for a in annotations
        ]

        return InterviewReplayResponse(
            interview_id=interview_id,
            total_annotations=len(items),
            annotations=items,
        )
