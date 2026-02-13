"""
MS4-IS2: Relationship Expansion Planner

Deterministic one-hop expansion of seed documents via outgoing relationships.

This module generates a RetrievalPlan (MS4-IS1) from a list of seed documents.
It only considers outgoing relationships and collects metadata for each expansion.

Non-goals:
- No recursive traversal
- No cycle detection
- No heuristics
- No filtering by relation_type
"""

from typing import List, Dict
from sqlalchemy.orm import Session

from src.core.crud.document_relationships import list_relationships_for_document
from src.core.retrieval.retrieval_plan import RetrievalPlan


def expand_relationships_one_hop(
    session: Session,
    seed_document_ids: List[str]
) -> RetrievalPlan:
    """
    Deterministically expand seed documents via outgoing relationships (one-hop).

    Args:
        session: SQLAlchemy Session, injected by caller (ADR-023 compliant).
        seed_document_ids: List of DocumentNode UUIDs to expand from.

    Returns:
        RetrievalPlan object containing:
            - seed_document_ids: original input
            - expanded_document_ids: all outgoing related document IDs
            - expansion_metadata: list of dicts with keys:
                * from_document_id
                * to_document_id
                * relation_type
    """
    expanded_ids = set()
    expansion_metadata: List[Dict[str, str]] = []

    # Ensure deterministic order
    sorted_seed_ids = sorted(seed_document_ids)

    for seed_id in sorted_seed_ids:
        # Only outgoing relationships
        relationships = list_relationships_for_document(
            session=session,
            document_id=seed_id,
            outgoing=True,
            incoming=False
        )

        # Collect related document IDs and metadata
        for rel in sorted(relationships, key=lambda r: r.to_document_id):
            expanded_ids.add(rel.to_document_id)
            expansion_metadata.append({
                "from_document_id": rel.from_document_id,
                "to_document_id": rel.to_document_id,
                "relation_type": rel.relation_type
            })

    # Remove seeds from expanded_ids if accidentally included
    expanded_ids.difference_update(seed_document_ids)

    return RetrievalPlan(
        seed_document_ids=seed_document_ids,
        expanded_document_ids=sorted(expanded_ids),
        expansion_metadata=expansion_metadata,
        constraints={"depth": 1, "traversal": "outgoing"}
    )
