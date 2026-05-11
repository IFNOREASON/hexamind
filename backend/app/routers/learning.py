from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.graph_node import GraphNode
from app.schemas.chat import MasteryStatsOut, SuggestionOut, DeadlineOut
from app.agents.suggestion_agent import run_suggestions

router = APIRouter(prefix="/api/learning", tags=["learning"])

# In-memory cache for suggestions
_suggestions_cache: list[SuggestionOut] = []
_suggestions_ready = False


@router.get("/mastery", response_model=MasteryStatsOut)
async def get_mastery(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(GraphNode.id)))).scalar() or 0
    mastered = (
        await db.execute(
            select(func.count(GraphNode.id)).where(GraphNode.mastery >= 0.7)
        )
    ).scalar() or 0
    needs_review = (
        await db.execute(
            select(func.count(GraphNode.id)).where(
                GraphNode.mastery > 0, GraphNode.mastery < 0.5
            )
        )
    ).scalar() or 0

    progress = round((mastered / total * 100) if total > 0 else 0, 1)
    return MasteryStatsOut(
        overall_progress=progress,
        total_concepts=total,
        mastered_concepts=mastered,
        needs_review=needs_review,
    )


@router.get("/suggestions", response_model=list[SuggestionOut])
async def get_suggestions(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Get learning suggestions. Returns cached suggestions immediately, 
    triggers background update if needed."""
    global _suggestions_cache, _suggestions_ready
    
    nodes_result = await db.execute(select(GraphNode))
    nodes = nodes_result.scalars().all()
    if not nodes:
        return []

    node_summaries = [
        {
            "name": n.name,
            "category": n.category,
            "mastery": n.mastery,
            "description": n.description,
            "id": n.id,
        }
        for n in nodes
    ]
    
    # If no cached suggestions, generate fallback immediately
    if not _suggestions_cache:
        _suggestions_cache = _generate_fallback_suggestions(node_summaries)
    
    # Trigger background update with LLM (non-blocking)
    if not _suggestions_ready:
        background_tasks.add_task(_update_suggestions_async, node_summaries)
    
    return _suggestions_cache


async def _update_suggestions_async(node_summaries: list[dict]):
    """Background task to update suggestions using LLM."""
    global _suggestions_cache, _suggestions_ready
    import asyncio
    
    try:
        raw = await asyncio.wait_for(
            run_suggestions(node_summaries),
            timeout=10.0
        )
        if raw:
            _suggestions_cache = [
                SuggestionOut(
                    id=i + 1,
                    type=s.get("type", "review"),
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                    target_node_id=s.get("target_node_id"),
                )
                for i, s in enumerate(raw)
            ]
            _suggestions_ready = True
    except Exception as e:
        # Keep fallback suggestions on error
        print(f"[Background] Failed to generate LLM suggestions: {e}")


def _generate_fallback_suggestions(node_summaries: list[dict]) -> list[SuggestionOut]:
    """Generate simple fallback suggestions without LLM."""
    suggestions = []
    
    # Find low mastery nodes
    low_mastery = [n for n in node_summaries if n.get("mastery", 0) < 0.5]
    medium_mastery = [n for n in node_summaries if 0.5 <= n.get("mastery", 0) < 0.7]
    
    if low_mastery:
        suggestions.append(SuggestionOut(
            id=1,
            type="strengthen",
            title=f"强化基础概念",
            description=f"有 {len(low_mastery)} 个概念掌握度较低，建议优先复习。",
            target_node_id=low_mastery[0].get("id")
        ))
    
    if medium_mastery:
        suggestions.append(SuggestionOut(
            id=2,
            type="review",
            title="巩固中等掌握度知识",
            description=f"{len(medium_mastery)} 个概念需要进一步巩固。",
            target_node_id=medium_mastery[0].get("id")
        ))
    
    if not suggestions:
        suggestions.append(SuggestionOut(
            id=1,
            type="explore",
            title="继续探索新知识",
            description="当前知识掌握良好，可以尝试学习新的相关内容。",
            target_node_id=None
        ))
    
    return suggestions


@router.get("/deadlines", response_model=list[DeadlineOut])
async def get_deadlines(db: AsyncSession = Depends(get_db)):
    """Placeholder: will be replaced with spaced repetition system."""
    return []
