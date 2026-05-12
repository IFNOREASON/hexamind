"""LangGraph Animation Generation Agent.

Generates animation concept and timeline based on knowledge node content.
"""

import json
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm
from app.constants import CULTIVATION_STAGES

logger = logging.getLogger(__name__)


class AnimationState(TypedDict):
    node_name: str
    node_description: str
    source_content: str
    current_stage: int
    difficulty: str
    concept: dict | None
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
        "easy": "动画应简洁直观，重点突出，适合初学者",
        "medium": "动画应包含一定深度，展示关键概念的工作原理",
        "hard": "动画应包含复杂流程和高级应用，适合进阶学习",
    }
    diff_desc = diff_map.get(difficulty, diff_map["medium"])

    return f"当前修炼境界：{_get_stage_name(stage)}期（第{stage + 1}阶段），内容深度：{level_desc}。{diff_desc}。"


ANIMATION_PROMPT = """你是一个专业的教育动画设计师，擅长设计生动的原理演示动画。根据以下知识内容，生成一份专业的动画设计方案。

知识主题：{node_name}
主题描述：{node_description}

参考资料内容：
{source_content}

动画设计要求：
{difficulty_guidance}

严格按照以下 JSON 格式返回（无markdown包裹）：
{{
  "title": "动画主标题",
  "animation_type": "principle_demo",
  "duration_minutes": 5,
  "target_audience": "目标受众描述",
  "core_concept": "核心概念简述",
  "visual_style": {{
    "color_scheme": ["#3B82F6", "#8B5CF6", "#10B981"],
    "animation_style": "2D_flat",
    "complexity_level": "medium"
  }},
  "timeline": [
    {{
      "time_start": 0,
      "time_end": 30,
      "scene_name": "场景名称",
      "description": "场景描述",
      "animations": [
        {{
          "element": "动画元素名称",
          "action": "动画动作（如：fade_in, move, rotate, morph）",
          "duration": 5,
          "start_delay": 0,
          "description": "详细动画描述"
        }}
      ],
      "voiceover": "配音文本",
      "on_screen_text": ["屏幕文字1", "屏幕文字2"]
    }}
  ],
  "key_frames": [
    {{
      "time": 15,
      "description": "关键帧描述",
      "visual_elements": ["元素1", "元素2"]
    }}
  ],
  "summary": {{
    "key_takeaways": ["核心要点1", "核心要点2"],
    "further_reading": "拓展学习建议"
  }}
}}

动画设计规范：
1. 总时长控制在3-10分钟
2. 时间轴包含5-15个时间片段
3. 每个时间片段20-60秒
4. 使用丰富的动画类型（淡入淡出、移动、旋转、变形等）
5. 从简单概念开始，逐步深入
6. 使用视觉化方式展示抽象概念
7. 最后进行知识总结
8. 使用中文撰写
9. 内容必须基于提供的参考资料

动画类型（animation_type）可选：
- principle_demo: 原理演示（最常用）
- process_flow: 流程展示
- comparison: 对比动画
- timeline_evolution: 时间线演变
- interactive_demo: 交互演示

视觉风格（animation_style）可选：
- 2D_flat: 2D扁平化
- 3D_modern: 3D现代风格
- hand_drawn: 手绘风格
- infographic: 信息图风格
- minimalist: 极简主义

复杂度（complexity_level）可选：
- simple: 简单，适合入门
- medium: 中等，适合一般学习
- complex: 复杂，适合深入理解"""


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


def _validate_concept(concept: dict) -> dict | None:
    """Validate and normalize animation concept."""
    if not isinstance(concept, dict):
        return None

    timeline = concept.get("timeline", [])
    if not isinstance(timeline, list) or len(timeline) < 3:
        return None

    validated_timeline = []
    for item in timeline:
        if not isinstance(item, dict):
            continue
        animations = item.get("animations", [])
        if not isinstance(animations, list):
            animations = []
        validated_animations = []
        for anim in animations:
            if isinstance(anim, dict):
                validated_animations.append({
                    "element": str(anim.get("element", "")),
                    "action": str(anim.get("action", "")),
                    "duration": int(anim.get("duration", 5)),
                    "start_delay": int(anim.get("start_delay", 0)),
                    "description": str(anim.get("description", "")),
                })
        validated_item = {
            "time_start": int(item.get("time_start", 0)),
            "time_end": int(item.get("time_end", 30)),
            "scene_name": str(item.get("scene_name", "")),
            "description": str(item.get("description", "")),
            "animations": validated_animations,
            "voiceover": str(item.get("voiceover", "")),
            "on_screen_text": item.get("on_screen_text", []) if isinstance(item.get("on_screen_text"), list) else [],
        }
        validated_timeline.append(validated_item)

    if len(validated_timeline) < 3:
        return None

    return {
        "title": concept.get("title", f"{concept.get('node_name', '')} - 动画演示"),
        "animation_type": concept.get("animation_type", "principle_demo"),
        "duration_minutes": int(concept.get("duration_minutes", 5)),
        "target_audience": concept.get("target_audience", ""),
        "core_concept": concept.get("core_concept", ""),
        "visual_style": concept.get("visual_style", {}),
        "timeline": validated_timeline,
        "key_frames": concept.get("key_frames", []) if isinstance(concept.get("key_frames"), list) else [],
        "summary": concept.get("summary", {}),
    }


async def generate_animation(state: AnimationState) -> AnimationState:
    """Generate animation concept from knowledge content."""
    source_content = state["source_content"] or ""
    if len(source_content) > 10000:
        source_content = source_content[:10000] + "\n...(内容已截断)"

    difficulty_guidance = _get_difficulty_guidance(
        state["current_stage"], state["difficulty"]
    )

    prompt = ANIMATION_PROMPT.format(
        node_name=state["node_name"],
        node_description=state["node_description"] or "无详细描述",
        source_content=source_content or "无参考资料",
        difficulty_guidance=difficulty_guidance,
    )

    llm = get_llm(temperature=0.4, content_type='animation')
    try:
        response = await llm.ainvoke([
            SystemMessage(content="你是一个专业的教育动画设计师，只返回 JSON 对象，不要包含任何其他文字。你擅长设计生动的原理演示动画，包含时间轴、动画效果和视觉指导。"),
            HumanMessage(content=prompt),
        ])
        content = response.content
        if isinstance(content, str):
            parsed = _parse_json_response(content)
            if parsed:
                concept = _validate_concept(parsed)
                if concept:
                    return {
                        **state,
                        "concept": concept,
                        "error": None
                    }
                return {**state, "concept": None, "error": "生成的动画概念格式不合法或时间轴片段不足"}
        return {**state, "concept": None, "error": "LLM 返回内容格式不正确"}
    except Exception as e:
        logger.error("Animation generation failed: %s", e)
        return {**state, "concept": None, "error": str(e)}


def build_animation_graph() -> StateGraph:
    graph = StateGraph(AnimationState)
    graph.add_node("generate_animation", generate_animation)
    graph.set_entry_point("generate_animation")
    graph.add_edge("generate_animation", END)
    return graph


animation_graph = build_animation_graph().compile()


async def run_animation_generation(
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
) -> dict | None:
    """Run animation generation agent and return animation concept."""
    state: AnimationState = {
        "node_name": node_name,
        "node_description": node_description,
        "source_content": source_content,
        "current_stage": current_stage,
        "difficulty": difficulty,
        "concept": None,
        "error": None,
    }
    result = await animation_graph.ainvoke(state)
    return result["concept"]
