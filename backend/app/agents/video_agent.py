"""LangGraph Video Generation Agent.

Generates video script based on knowledge node content with RAG retrieval.
"""

import json
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm
from app.constants import CULTIVATION_STAGES

logger = logging.getLogger(__name__)


class VideoState(TypedDict):
    node_name: str
    node_description: str
    source_content: str
    current_stage: int
    difficulty: str
    script: dict | None
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
        "easy": "视频内容应简洁明了，重点突出，适合初学者",
        "medium": "视频内容应包含一定深度，涵盖关键概念和应用案例",
        "hard": "视频内容应包含高级应用和复杂案例，适合进阶学习",
    }
    diff_desc = diff_map.get(difficulty, diff_map["medium"])

    return f"当前修炼境界：{_get_stage_name(stage)}期（第{stage + 1}阶段），内容深度：{level_desc}。{diff_desc}。"


VIDEO_PROMPT = """你是一个专业的教学视频制作专家，擅长设计高质量的讲解视频脚本。根据以下知识内容，生成一份专业的视频讲解脚本。

知识主题：{node_name}
主题描述：{node_description}

参考资料内容：
{source_content}

视频设计要求：
{difficulty_guidance}

严格按照以下 JSON 格式返回（无markdown包裹）：
{{
  "title": "视频主标题",
  "duration_minutes": 15,
  "target_audience": "目标受众描述",
  "learning_objectives": ["学习目标1", "学习目标2", "学习目标3"],
  "scenes": [
    {{
      "scene_id": 1,
      "title": "场景标题",
      "duration_seconds": 60,
      "visual": "视觉画面描述（包括场景布局、动画效果、图表类型等）",
      "narration": "旁白文本内容",
      "onscreen_text": "屏幕上显示的关键文字",
      "broll": "B-roll画面描述（补充画面）"
    }}
  ],
  "summary_scene": {{
    "title": "总结",
    "key_points": ["核心要点1", "核心要点2"],
    "next_steps": "下一步学习建议"
  }}
}}

视频设计规范：
1. 总时长控制在10-20分钟
2. 场景数量控制在8-15个
3. 每个场景时长30-120秒
4. 开场场景介绍主题和学习目标
5. 中间场景逐步深入讲解核心概念
6. 使用丰富的视觉描述（图表、动画、演示等）
7. 最后场景进行知识总结和回顾
8. 使用中文撰写
9. 内容必须基于提供的参考资料

旁白要求：
- 语言清晰、专业、易于理解
- 节奏适中，适合学习
- 避免过于口语化
- 关键概念适当强调

视觉设计要求：
- 提供具体的画面描述
- 包含图表类型建议
- 包含动画效果建议
- 包含场景切换建议"""


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


def _validate_script(script: dict) -> dict | None:
    """Validate and normalize video script."""
    if not isinstance(script, dict):
        return None

    scenes = script.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) < 3:
        return None

    validated_scenes = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        validated_scene = {
            "scene_id": scene.get("scene_id", len(validated_scenes) + 1),
            "title": str(scene.get("title", "")),
            "duration_seconds": int(scene.get("duration_seconds", 60)),
            "visual": str(scene.get("visual", "")),
            "narration": str(scene.get("narration", "")),
            "onscreen_text": str(scene.get("onscreen_text", "")),
            "broll": str(scene.get("broll", "")),
        }
        validated_scenes.append(validated_scene)

    if len(validated_scenes) < 3:
        return None

    return {
        "title": script.get("title", f"{script.get('node_name', '')} - 讲解视频"),
        "duration_minutes": int(script.get("duration_minutes", 15)),
        "target_audience": script.get("target_audience", ""),
        "learning_objectives": script.get("learning_objectives", []),
        "scenes": validated_scenes,
        "summary_scene": script.get("summary_scene", {}),
    }


async def generate_video(state: VideoState) -> VideoState:
    """Generate video script from knowledge content."""
    source_content = state["source_content"] or ""
    if len(source_content) > 10000:
        source_content = source_content[:10000] + "\n...(内容已截断)"

    difficulty_guidance = _get_difficulty_guidance(
        state["current_stage"], state["difficulty"]
    )

    prompt = VIDEO_PROMPT.format(
        node_name=state["node_name"],
        node_description=state["node_description"] or "无详细描述",
        source_content=source_content or "无参考资料",
        difficulty_guidance=difficulty_guidance,
    )

    llm = get_llm(temperature=0.3, content_type='video')
    try:
        response = await llm.ainvoke([
            SystemMessage(content="你是一个专业的教学视频制作专家，只返回 JSON 对象，不要包含任何其他文字。你擅长设计精美的视频脚本，包含场景描述、旁白文本和视觉指导。"),
            HumanMessage(content=prompt),
        ])
        content = response.content
        if isinstance(content, str):
            parsed = _parse_json_response(content)
            if parsed:
                script = _validate_script(parsed)
                if script:
                    return {
                        **state,
                        "script": script,
                        "error": None
                    }
                return {**state, "script": None, "error": "生成的脚本格式不合法或场景数量不足"}
        return {**state, "script": None, "error": "LLM 返回内容格式不正确"}
    except Exception as e:
        logger.error("Video generation failed: %s", e)
        return {**state, "script": None, "error": str(e)}


def build_video_graph() -> StateGraph:
    graph = StateGraph(VideoState)
    graph.add_node("generate_video", generate_video)
    graph.set_entry_point("generate_video")
    graph.add_edge("generate_video", END)
    return graph


video_graph = build_video_graph().compile()


async def run_video_generation(
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
) -> dict | None:
    """Run video generation agent and return video script."""
    state: VideoState = {
        "node_name": node_name,
        "node_description": node_description,
        "source_content": source_content,
        "current_stage": current_stage,
        "difficulty": difficulty,
        "script": None,
        "error": None,
    }
    result = await video_graph.ainvoke(state)
    return result["script"]