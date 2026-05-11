"""Persist extraction results to database with deduplication layer 2 (idempotent add)."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph_node import GraphNode
from app.models.graph_edge import GraphEdge
from app.models.hyperedge import Hyperedge

logger = logging.getLogger(__name__)


async def persist_extraction(
    nodes: list[dict],
    edges: list[dict],
    hyperedges: list[dict],
    db: AsyncSession,
) -> dict[str, int]:
    """Write extraction results to database.

    Dedup layer 2: idempotent - skip existing node IDs.
    Returns counts of inserted items.
    """
    added_nodes = 0
    added_edges = 0
    added_hyper = 0

    # Nodes: idempotent add by primary key
    existing_ids = set()
    if nodes:
        result = await db.execute(select(GraphNode.id))
        existing_ids = {row[0] for row in result}

    for node_data in nodes:
        if node_data["id"] in existing_ids:
            continue  # Dedup layer 2: skip existing
        db.add(GraphNode(**node_data))
        existing_ids.add(node_data["id"])
        added_nodes += 1

    # Edges: check for duplicate (source, target, relationship)
    for edge_data in edges:
        src = edge_data["source_node_id"]
        tgt = edge_data["target_node_id"]
        rel = edge_data["relationship"]
        existing = await db.execute(
            select(GraphEdge.id).where(
                GraphEdge.source_node_id == src,
                GraphEdge.target_node_id == tgt,
                GraphEdge.relationship == rel,
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue
        db.add(GraphEdge(**edge_data))
        added_edges += 1

    # Hyperedges
    for he_data in hyperedges:
        db.add(Hyperedge(**he_data))
        added_hyper += 1

    await db.commit()

    logger.info(
        "Persisted: %d nodes, %d edges, %d hyperedges",
        added_nodes, added_edges, added_hyper,
    )
    return {"nodes": added_nodes, "edges": added_edges, "hyperedges": added_hyper}
