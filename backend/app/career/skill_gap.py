"""
Skill Gap Analyzer.
Identifies missing concepts for candidate weak topics (e.g. Redis Persistence, Redis Cluster, Eviction Policies).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.career.schemas import SkillGapItem, SkillGapResponse
from app.models.candidate_memory import SkillProgress


class SkillGapAnalyzer:
    """Analyzes candidate skill progression to identify specific missing concepts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def analyze_skill_gaps(self, candidate_id: str) -> SkillGapResponse:
        skills = self.db.query(SkillProgress).filter(SkillProgress.candidate_id == candidate_id).all()
        weak_skills = [s for s in skills if s.current_score < 70.0]

        concept_mapping = {
            "redis": ["Redis Persistence (RDB/AOF)", "Redis Cluster Sharding", "Eviction Policies (LRU/LFU)", "Pub/Sub Messaging", "Redis Streams"],
            "kafka": ["Partition Rebalancing", "Consumer Group Offset Commit", "Log Compaction", "Idempotent Producer", "ISR Replica Sync"],
            "postgresql": ["B-Tree vs GIN Indexes", "MVCC & Vacuum Optimization", "WAL Replication Lag", "Connection Pooling (PgBouncer)", "EXPLAIN ANALYZE tuning"],
            "system design": ["Distributed Consensus (Raft/Paxos)", "Consistent Hashing", "Rate Limiting Algorithms", "CQRS Architecture", "Event Sourcing"],
            "python": ["Asyncio Event Loop Lifecycle", "GIL Mutex Implications", "Metaclasses & Decorators", "Memory Profiling & Leaks", "Generators vs Iterators"],
        }

        gaps = []
        if not weak_skills:
            # Default analysis
            for topic, concepts in list(concept_mapping.items())[:2]:
                gaps.append(
                    SkillGapItem(
                        topic=topic.capitalize(),
                        severity="MEDIUM",
                        missing_concepts=concepts[:3],
                    )
                )
        else:
            for s in weak_skills:
                key = s.skill_name.lower()
                concepts = concept_mapping.get(key, ["Advanced Tuning", "Cluster Deployment", "Failover Recovery", "Performance Metrics"])
                gaps.append(
                    SkillGapItem(
                        topic=s.skill_name,
                        severity="HIGH" if s.current_score < 60.0 else "MEDIUM",
                        missing_concepts=concepts,
                    )
                )

        return SkillGapResponse(
            candidate_id=candidate_id,
            total_gaps=len(gaps),
            gaps=gaps,
        )
