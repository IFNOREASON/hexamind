from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.graph_node import GraphNode
from app.models.graph_edge import GraphEdge
from app.models.hyperedge import Hyperedge
from app.schemas.graph import GraphOut, NodeOut, EdgeOut, HyperedgeOut

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("", response_model=GraphOut)
async def get_full_graph(db: AsyncSession = Depends(get_db)):
    nodes = (await db.execute(select(GraphNode))).scalars().all()
    edges = (await db.execute(select(GraphEdge))).scalars().all()
    hyperedges = (await db.execute(select(Hyperedge))).scalars().all()
    return GraphOut(
        nodes=[NodeOut.model_validate(n) for n in nodes],
        edges=[EdgeOut.model_validate(e) for e in edges],
        hyperedges=[HyperedgeOut.model_validate(h) for h in hyperedges],
    )


@router.get("/source/{source_id}", response_model=GraphOut)
async def get_graph_by_source(source_id: int, db: AsyncSession = Depends(get_db)):
    nodes = (
        await db.execute(select(GraphNode).where(GraphNode.source_id == source_id))
    ).scalars().all()
    node_ids = {n.id for n in nodes}

    edges = (await db.execute(select(GraphEdge))).scalars().all()
    filtered_edges = [
        e for e in edges if e.source_node_id in node_ids or e.target_node_id in node_ids
    ]

    hyperedges = (await db.execute(select(Hyperedge))).scalars().all()
    filtered_hyper = [
        h for h in hyperedges if any(nid in node_ids for nid in (h.node_ids or []))
    ]

    return GraphOut(
        nodes=[NodeOut.model_validate(n) for n in nodes],
        edges=[EdgeOut.model_validate(e) for e in filtered_edges],
        hyperedges=[HyperedgeOut.model_validate(h) for h in filtered_hyper],
    )
