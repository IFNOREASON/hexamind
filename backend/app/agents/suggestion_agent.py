"""LangGraph Learning Suggestion Agent.

Analyzes mastery levels and generates personalized learning suggestions.
"""

import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm

logger = logging.getLogger(__name__)


class SuggestionState(TypedDict):
    node_summaries: list[dict]  # [{name, category, mastery, description}]
    suggestions: list[dict]  # [{type, title, description, target_node_id}]


SUGGESTION_PROMPT = """你是一个智能学习顾问。根据用户的知识图谱掌握情况，生成 3-5 条学习建议。

当前知识节点掌握情况：
{nodes_info}

要求：
1. 针对低掌握度（<50%）的节点提供强化建议
2. 建议学习路径和优先级
3. 识别知识盲区

返回 JSON 数组（无 markdown）：
[{{"type": "strengthen|review|explore", "title": "标题", "description": "描述", "target_node_id": "节点ID或null"}}]"""


async def generate_suggestions(state: SuggestionState) -> SuggestionState:
    """Generate learning suggestions based on mastery data."""
    import asyncio
    
    if not state["node_summaries"]:
        return {**state, "suggestions": []}

    nodes_info = "\n".join(
        f"- {n['name']} [{n['category']}]: 掌握度 {n['mastery']*100:.0f}% - {n['description'][:50]}"
        for n in state["node_summaries"]
    )

    llm = get_llm(temperature=0.5)
    try:
        response = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content="你是一个学习建议生成器，只返回JSON数组。"),
                HumanMessage(content=SUGGESTION_PROMPT.format(nodes_info=nodes_info)),
            ]),
            timeout=30.0  # 30 seconds timeout for suggestions
        )
        content = response.content
        if isinstance(content, str):
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            if content.startswith("json"):
                content = content[4:].strip()

            import json
            suggestions = json.loads(content)
            if isinstance(suggestions, list):
                return {**state, "suggestions": suggestions}
    except asyncio.TimeoutError:
        logger.error("Suggestion generation timed out")
    except Exception as e:
        logger.error("Suggestion generation failed: %s", e)

    return {**state, "suggestions": []}


def build_suggestion_graph() -> StateGraph:
    graph = StateGraph(SuggestionState)
    graph.add_node("generate_suggestions", generate_suggestions)
    graph.set_entry_point("generate_suggestions")
    graph.add_edge("generate_suggestions", END)
    return graph


suggestion_graph = build_suggestion_graph().compile()


async def run_suggestions(node_summaries: list[dict]) -> list[dict]:
    """Run suggestion agent and return list of suggestions."""
    state: SuggestionState = {
        "node_summaries": node_summaries,
        "suggestions": [],
    }
    result = await suggestion_graph.ainvoke(state)
    return result["suggestions"]
