"""
Interview Knowledge Graph Engine.
Manages graph relationships connecting Candidate -> Interview -> Skill -> Question -> Evaluation -> Weakness -> Learning Plan.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.career import KnowledgeGraphEdge, KnowledgeGraphNode


class KnowledgeGraphEngine:
    """Manages knowledge graph nodes and edges across candidate interviews and skills."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add_node(self, node_type: str, label: str, properties: Optional[Dict[str, Any]] = None) -> KnowledgeGraphNode:
        node = KnowledgeGraphNode(
            node_type=node_type,
            label=label,
            properties_json=json.dumps(properties or {}),
        )
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def add_edge(self, source_id: str, target_id: str, relation_type: str) -> KnowledgeGraphEdge:
        edge = KnowledgeGraphEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
        )
        self.db.add(edge)
        self.db.commit()
        self.db.refresh(edge)
        return edge

    def get_candidate_knowledge_subgraph(self, candidate_id: str) -> Dict[str, Any]:
        nodes = self.db.query(KnowledgeGraphNode).limit(50).all()
        edges = self.db.query(KnowledgeGraphEdge).limit(50).all()
        return {
            "candidate_id": candidate_id,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "nodes": [{"id": n.id, "type": n.node_type, "label": n.label} for n in nodes],
            "edges": [{"id": e.id, "source": e.source_id, "target": e.target_id, "relation": e.relation_type} for e in edges],
        }
