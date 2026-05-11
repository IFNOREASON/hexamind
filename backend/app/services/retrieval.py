"""Simple retrieval service for RAG: keyword + TF-IDF matching against graph nodes and source text."""

import logging
import math
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph_node import GraphNode
from app.models.source import Source

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """Simple tokenization: split on non-alphanumeric, keep Chinese chars."""
    import re
    tokens = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
    return tokens


def _tfidf_score(query_tokens: list[str], doc_tokens: list[str]) -> float:
    """Compute simple TF-IDF relevance score."""
    if not doc_tokens or not query_tokens:
        return 0.0
    doc_counter = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    score = 0.0
    for token in query_tokens:
        tf = doc_counter.get(token, 0) / doc_len
        score += tf  # Simplified: no IDF across corpus
    return score


async def retrieve_context(query: str, db: AsyncSession, top_k: int = 5) -> str:
    """Retrieve relevant knowledge context for a query."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return ""

    # Search graph nodes
    nodes_result = await db.execute(select(GraphNode))
    nodes = nodes_result.scalars().all()

    scored_nodes: list[tuple[float, str]] = []
    for node in nodes:
        doc_text = f"{node.name} {node.description} {node.category}"
        doc_tokens = _tokenize(doc_text)
        score = _tfidf_score(query_tokens, doc_tokens)
        # Bonus for exact name match
        if any(t in node.name.lower() for t in query_tokens):
            score += 2.0
        if score > 0:
            scored_nodes.append((score, f"[{node.category}] {node.name}: {node.description}"))

    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    context_parts = [text for _, text in scored_nodes[:top_k]]

    # Also search source content snippets
    sources_result = await db.execute(
        select(Source).where(Source.content_text.isnot(None))
    )
    sources = sources_result.scalars().all()

    for source in sources:
        content = source.content_text or ""
        # Find relevant snippets (paragraphs containing query terms)
        paragraphs = content.split("\n\n")
        for para in paragraphs[:50]:  # Limit search scope
            para_tokens = _tokenize(para)
            score = _tfidf_score(query_tokens, para_tokens)
            if score > 0.1:
                snippet = para[:300]
                scored_nodes.append((score, f"[来源: {source.name}] {snippet}"))

    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    all_contexts = [text for _, text in scored_nodes[:top_k]]

    if not all_contexts:
        return ""

    return "相关知识：\n" + "\n".join(f"- {ctx}" for ctx in all_contexts)
