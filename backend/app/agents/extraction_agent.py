"""Knowledge extraction Agent using LangGraph (graphify-inspired architecture).

Pipeline: detect_type → extract_entities → build_graph → deduplicate → detect_communities

Key features from graphify:
- Confidence scoring (EXTRACTED / INFERRED / AMBIGUOUS)
- SHA256 extraction caching
- Deterministic node ID (_make_id)
- 3-layer deduplication
- NetworkX graph construction
- Louvain community detection
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import TypedDict, Annotated

import networkx as nx
from langgraph.graph import StateGraph, END

from app.config import settings
from app.services.llm import get_llm

logger = logging.getLogger(__name__)


# ── State ──────────────────────────────────────────────

class ExtractionState(TypedDict):
    source_id: int
    source_type: str
    content_text: str
    content_hash: str
    # Extracted raw entities/relations from LLM
    raw_entities: list[dict]
    raw_relations: list[dict]
    raw_hyperedges: list[dict]
    # Built graph data
    nodes: list[dict]
    edges: list[dict]
    hyperedges: list[dict]
    # Community detection results
    communities: dict[str, int]
    error: str | None


# ── Helpers ────────────────────────────────────────────

def _make_id(name: str, category: str) -> str:
    """Deterministic node ID generation (from graphify _make_id pattern)."""
    key = f"{name.lower().strip()}::{category.lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def _get_cache_path(content_hash: str) -> Path:
    return settings.extraction_cache_dir / f"{content_hash}.json"


CATEGORY_COLORS = {
    "concept": "#60a5fa",
    "technology": "#a78bfa",
    "framework": "#c084fc",
    "language": "#34d399",
    "tool": "#fbbf24",
    "person": "#f87171",
    "organization": "#fb923c",
    "event": "#e879f9",
}


# ── Node: Check Cache ─────────────────────────────────

def check_cache(state: ExtractionState) -> ExtractionState:
    """Check if extraction result is already cached (SHA256-based)."""
    cache_path = _get_cache_path(state["content_hash"])
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            logger.info("Cache hit for %s", state["content_hash"][:8])
            return {
                **state,
                "raw_entities": cached.get("entities", []),
                "raw_relations": cached.get("relations", []),
                "raw_hyperedges": cached.get("hyperedges", []),
            }
        except Exception:
            pass
    return state


# ── Node: LLM Extract ─────────────────────────────────

EXTRACTION_PROMPT = """You are a knowledge extraction expert. Analyze the following text and extract:

1. **Entities**: Knowledge concepts, technologies, people, organizations, events, etc.
2. **Relations**: Relationships between entities (directed edges).
3. **Hyperedges**: Group relationships involving 3+ entities.

For each entity, provide:
- name: concise name
- category: one of [concept, technology, framework, language, tool, person, organization, event]
- description: brief description (1-2 sentences)
- confidence: EXTRACTED (explicitly stated), INFERRED (implied), or AMBIGUOUS (uncertain)
- confidence_score: 0.0-1.0

For each relation, provide:
- source: source entity name (exact match)
- target: target entity name (exact match)
- relationship: description of the relationship
- confidence: EXTRACTED/INFERRED/AMBIGUOUS
- confidence_score: 0.0-1.0

For each hyperedge (group of 3+ entities with shared relationship):
- entities: list of entity names
- relation: the shared relationship
- label: concise label
- confidence: EXTRACTED/INFERRED/AMBIGUOUS
- confidence_score: 0.0-1.0

Return JSON only (no markdown):
{{"entities": [...], "relations": [...], "hyperedges": [...]}}

Text to analyze:
---
{text}
---"""


async def llm_extract(state: ExtractionState) -> ExtractionState:
    """Extract entities and relations using LLM (with structured JSON output)."""
    import asyncio
    
    if state["raw_entities"]:
        return state  # Already extracted (from cache)

    text = state["content_text"]
    # Truncate very long texts to reduce LLM processing time
    if len(text) > 8000:
        text = text[:8000] + "\n...[内容已截断，仅处理前8000字符]"
        logger.warning(f"Text truncated from {len(state['content_text'])} to 8000 chars")

    llm = get_llm(temperature=0.1)
    try:
        # Add timeout protection for LLM call
        response = await asyncio.wait_for(
            llm.ainvoke(EXTRACTION_PROMPT.format(text=text)),
            timeout=180.0  # 3 minutes timeout for extraction
        )
        content = response.content
        if isinstance(content, str):
            # Strip markdown code fences if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            if content.startswith("json"):
                content = content[4:].strip()
            parsed = json.loads(content)
        else:
            parsed = {"entities": [], "relations": [], "hyperedges": []}

        # Cache the extraction
        cache_path = _get_cache_path(state["content_hash"])
        cache_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            **state,
            "raw_entities": parsed.get("entities", []),
            "raw_relations": parsed.get("relations", []),
            "raw_hyperedges": parsed.get("hyperedges", []),
        }
    except asyncio.TimeoutError:
        error_msg = "LLM extraction timed out (120s limit)"
        logger.error(error_msg)
        return {**state, "error": error_msg}
    except Exception as e:
        logger.error("LLM extraction failed: %s", e)
        return {**state, "error": str(e)}


# ── Node: Build Graph ─────────────────────────────────

def build_graph(state: ExtractionState) -> ExtractionState:
    """Build nodes/edges from raw extraction (with deduplication layer 1: within-source)."""
    if state.get("error"):
        return state

    seen_ids: set[str] = set()
    nodes = []
    name_to_id: dict[str, str] = {}

    for entity in state["raw_entities"]:
        name = entity.get("name", "").strip()
        category = entity.get("category", "concept").lower()
        if not name:
            continue

        node_id = _make_id(name, category)
        if node_id in seen_ids:
            continue  # Dedup layer 1: within-source
        seen_ids.add(node_id)
        name_to_id[name.lower()] = node_id

        confidence_score = float(entity.get("confidence_score", 0.8))
        nodes.append({
            "id": node_id,
            "name": name,
            "description": entity.get("description", ""),
            "category": category,
            "color": CATEGORY_COLORS.get(category, "#94a3b8"),
            "size": 0.5 + confidence_score,
            "source_id": state["source_id"],
            "source_type": state["source_type"],
            "community_id": None,
            "mastery": 0.0,
        })

    edges = []
    for rel in state["raw_relations"]:
        src_name = rel.get("source", "").strip().lower()
        tgt_name = rel.get("target", "").strip().lower()
        src_id = name_to_id.get(src_name)
        tgt_id = name_to_id.get(tgt_name)
        if not src_id or not tgt_id or src_id == tgt_id:
            continue

        edges.append({
            "source_node_id": src_id,
            "target_node_id": tgt_id,
            "relationship": rel.get("relationship", "related_to"),
            "confidence": rel.get("confidence", "EXTRACTED"),
            "confidence_score": float(rel.get("confidence_score", 0.8)),
            "weight": float(rel.get("confidence_score", 0.8)),
        })

    hyperedges = []
    for he in state["raw_hyperedges"]:
        entity_names = he.get("entities", [])
        node_ids = [
            name_to_id[n.lower()]
            for n in entity_names
            if n.lower() in name_to_id
        ]
        if len(node_ids) < 3:
            continue
        hyperedges.append({
            "label": he.get("label", ""),
            "relation": he.get("relation", ""),
            "confidence": he.get("confidence", "INFERRED"),
            "confidence_score": float(he.get("confidence_score", 0.6)),
            "node_ids": node_ids,
        })

    return {
        **state,
        "nodes": nodes,
        "edges": edges,
        "hyperedges": hyperedges,
    }


# ── Node: Community Detection ─────────────────────────

def detect_communities(state: ExtractionState) -> ExtractionState:
    """Detect communities using Louvain algorithm on NetworkX graph."""
    if state.get("error") or not state["nodes"]:
        return state

    G = nx.Graph()
    for node in state["nodes"]:
        G.add_node(node["id"])
    for edge in state["edges"]:
        G.add_edge(
            edge["source_node_id"],
            edge["target_node_id"],
            weight=edge["weight"],
        )

    communities: dict[str, int] = {}
    if len(G.nodes) > 1 and len(G.edges) > 0:
        try:
            from community import community_louvain
            partition = community_louvain.best_partition(G)
            communities = partition
        except Exception as e:
            logger.warning("Community detection failed: %s", e)
            # Fallback: assign all to community 0
            communities = {nid: 0 for nid in G.nodes}
    else:
        communities = {n["id"]: 0 for n in state["nodes"]}

    # Update node community assignments
    for node in state["nodes"]:
        node["community_id"] = communities.get(node["id"], 0)

    return {**state, "communities": communities}


# ── Graph Definition ──────────────────────────────────

def should_extract(state: ExtractionState) -> str:
    """Route: skip LLM if cache provided entities."""
    if state["raw_entities"]:
        return "build_graph"
    return "llm_extract"


def build_extraction_graph() -> StateGraph:
    """Build the LangGraph extraction pipeline."""
    graph = StateGraph(ExtractionState)

    graph.add_node("check_cache", check_cache)
    graph.add_node("llm_extract", llm_extract)
    graph.add_node("build_graph", build_graph)
    graph.add_node("detect_communities", detect_communities)

    graph.set_entry_point("check_cache")
    graph.add_conditional_edges("check_cache", should_extract, {
        "llm_extract": "llm_extract",
        "build_graph": "build_graph",
    })
    graph.add_edge("llm_extract", "build_graph")
    graph.add_edge("build_graph", "detect_communities")
    graph.add_edge("detect_communities", END)

    return graph


# Compiled graph (singleton)
extraction_graph = build_extraction_graph().compile()


async def run_extraction(
    source_id: int,
    source_type: str,
    content_text: str,
    content_hash: str,
) -> ExtractionState:
    """Run the extraction pipeline for a parsed source."""
    initial_state: ExtractionState = {
        "source_id": source_id,
        "source_type": source_type,
        "content_text": content_text,
        "content_hash": content_hash,
        "raw_entities": [],
        "raw_relations": [],
        "raw_hyperedges": [],
        "nodes": [],
        "edges": [],
        "hyperedges": [],
        "communities": {},
        "error": None,
    }
    result = await extraction_graph.ainvoke(initial_state)
    return result
