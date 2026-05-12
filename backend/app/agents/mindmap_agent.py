"""LangGraph MindMap Generation Agent.

Generates mind map structure based on knowledge node content.
"""

import json
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm
from app.constants import CULTIVATION_STAGES

logger = logging.getLogger(__name__)


class MindMapState(TypedDict):
    node_name: str
    node_description: str
    source_content: str
    current_stage: int
    difficulty: str
    mindmap: dict | None
    error: str | None


def _get_stage_name(stage: int) -> str:
    if 0 <= stage < len(CULTIVATION_STAGES):
        return CULTIVATION_STAGES[stage]["name"]
    return "凡人"


def _get_difficulty_guidance(stage: int, difficulty: str) -> str:
    if stage <= 2:
        level_desc = "基础入门，适合初学者理解"
    elif stage <= 5:
        level_desc = "进阶应用，需要综合运用知识"
    elif stage <= 8:
        level_desc = "深度解析，需要深度思考和实践"
    else:
        level_desc = "专家级，考察知识的融会贯通"

    diff_map = {
        "easy": "思维导图应简洁明了，重点突出，适合初学者",
        "medium": "思维导图应包含一定深度，涵盖关键概念和关联",
        "hard": "思维导图应包含高级概念和复杂关联，适合进阶学习",
    }
    diff_desc = diff_map.get(difficulty, diff_map["medium"])

    return f"当前修炼境界：{_get_stage_name(stage)}期（第{stage + 1}阶段），内容深度：{level_desc}。{diff_desc}。"


MINDMAP_PROMPT = """你是一个专业的知识架构师，擅长设计清晰的思维导图。根据以下知识内容，生成一份专业的思维导图。

知识主题：{node_name}
主题描述：{node_description}

参考资料内容：
{source_content}

思维导图设计要求：
{difficulty_guidance}

严格按照以下 JSON 格式返回（无markdown包裹）：
{{
  "title": "思维导图主标题",
  "root_node": {{
    "id": "root",
    "label": "中心主题",
    "description": "中心节点描述"
  }},
  "nodes": [
    {{
      "id": "node_1",
      "label": "节点标签",
      "description": "节点详细描述",
      "parent_id": "root",
      "level": 1,
      "color": "#3B82F6",
      "icon": "concept",
      "importance": "high"
    }}
  ],
  "edges": [
    {{
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "label": "关联描述",
      "relation_type": "belongs_to"
    }}
  ],
  "layout_config": {{
    "type": "radial",
    "direction": "RIGHT",
    "spacing": 100
  }},
  "legend": {{
    "colors": {{
      "#3B82F6": "核心概念",
      "#8B5CF6": "子概念",
      "#10B981": "实例",
      "#F59E0B": "注意事项"
    }},
    "icons": {{
      "concept": "概念",
      "example": "例子",
      "tip": "提示",
      "warning": "警告"
    }}
  }}
}}

思维导图设计规范：
1. 节点总数控制在15-40个
2. 层级深度控制在3-5层
3. 根节点1个，一级节点4-8个
4. 每个节点有清晰的标签和描述
5. 使用不同颜色区分节点类型
6. 使用不同图标标识节点性质
7. 建立清晰的关联关系
8. 使用中文撰写
9. 内容必须基于提供的参考资料

布局类型（type）可选：
- radial: 放射状
- tree: 树状
- mindmap: 思维导图（默认）
- org_chart: 组织结构图

关系类型（relation_type）可选：
- belongs_to: 属于
- depends_on: 依赖
- leads_to: 导致
- is_example_of: 是...的例子
- contrasts_with: 与...对比
- related_to: 相关联

重要性（importance）可选：
- high: 高
- medium: 中
- low: 低"""


def _parse_json_response(content: str) -> dict | None:
    """Parse LLM response, stripping markdown fences if present."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    if content.startswith("json"):
        content = content[4:].strip()

    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return None


def _validate_mindmap(mindmap: dict) -> dict | None:
    """Validate and normalize mind map."""
    if not isinstance(mindmap, dict):
        return None

    nodes = mindmap.get("nodes", [])
    if not isinstance(nodes, list) or len(nodes) < 5:
        return None

    validated_nodes = []
    node_ids = set()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", f"node_{len(validated_nodes)}"))
        if node_id in node_ids:
            node_id = f"{node_id}_{len(validated_nodes)}"
        node_ids.add(node_id)
        validated_node = {
            "id": node_id,
            "label": str(node.get("label", "")),
            "description": str(node.get("description", "")),
            "parent_id": str(node.get("parent_id", "root")),
            "level": int(node.get("level", 1)),
            "color": str(node.get("color", "#3B82F6")),
            "icon": str(node.get("icon", "concept")),
            "importance": str(node.get("importance", "medium")),
        }
        validated_nodes.append(validated_node)

    if len(validated_nodes) < 5:
        return None

    edges = mindmap.get("edges", [])
    if not isinstance(edges, list):
        edges = []
    validated_edges = []
    edge_ids = set()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        edge_id = str(edge.get("id", f"edge_{len(validated_edges)}"))
        if edge_id in edge_ids:
            edge_id = f"{edge_id}_{len(validated_edges)}"
        edge_ids.add(edge_id)
        validated_edge = {
            "id": edge_id,
            "source": str(edge.get("source", "")),
            "target": str(edge.get("target", "")),
            "label": str(edge.get("label", "")),
            "relation_type": str(edge.get("relation_type", "related_to")),
        }
        validated_edges.append(validated_edge)

    return {
        "title": mindmap.get("title", f"{mindmap.get('node_name', '')} - 思维导图"),
        "root_node": mindmap.get("root_node", {}),
        "nodes": validated_nodes,
        "edges": validated_edges,
        "layout_config": mindmap.get("layout_config", {}),
        "legend": mindmap.get("legend", {}),
    }


async def generate_mindmap(state: MindMapState) -> MindMapState:
    """Generate mind map from knowledge content."""
    source_content = state["source_content"] or ""
    if len(source_content) > 10000:
        source_content = source_content[:10000] + "\n...(内容已截断)"

    difficulty_guidance = _get_difficulty_guidance(
        state["current_stage"], state["difficulty"]
    )

    prompt = MINDMAP_PROMPT.format(
        node_name=state["node_name"],
        node_description=state["node_description"] or "无详细描述",
        source_content=source_content or "无参考资料",
        difficulty_guidance=difficulty_guidance,
    )

    llm = get_llm(temperature=0.2, content_type='mindmap')
    try:
        response = await llm.ainvoke([
            SystemMessage(content="你是一个专业的知识架构师，只返回 JSON 对象，不要包含任何其他文字。你擅长设计清晰的思维导图，包含节点、关联和布局配置。"),
            HumanMessage(content=prompt),
        ])
        content = response.content
        if isinstance(content, str):
            parsed = _parse_json_response(content)
            if parsed:
                mindmap = _validate_mindmap(parsed)
                if mindmap:
                    return {
                        **state,
                        "mindmap": mindmap,
                        "error": None
                    }
                return {**state, "mindmap": None, "error": "生成的思维导图格式不合法或节点数量不足"}
        return {**state, "mindmap": None, "error": "LLM 返回内容格式不正确"}
    except Exception as e:
        logger.error("Mind map generation failed: %s", e)
        return {**state, "mindmap": None, "error": str(e)}


def build_mindmap_graph() -> StateGraph:
    graph = StateGraph(MindMapState)
    graph.add_node("generate_mindmap", generate_mindmap)
    graph.set_entry_point("generate_mindmap")
    graph.add_edge("generate_mindmap", END)
    return graph


mindmap_graph = build_mindmap_graph().compile()


async def run_mindmap_generation(
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
) -> dict | None:
    """Run mind map generation agent and return mind map structure."""
    state: MindMapState = {
        "node_name": node_name,
        "node_description": node_description,
        "source_content": source_content,
        "current_stage": current_stage,
        "difficulty": difficulty,
        "mindmap": None,
        "error": None,
    }
    result = await mindmap_graph.ainvoke(state)
    return result["mindmap"]
