"""LangGraph Podcast Generation Agent.

Generates podcast script based on knowledge node content.
"""

import json
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm
from app.constants import CULTIVATION_STAGES

logger = logging.getLogger(__name__)


class PodcastState(TypedDict):
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
        "easy": "播客内容应简洁明了，重点突出，适合初学者",
        "medium": "播客内容应包含一定深度，涵盖关键概念和应用案例",
        "hard": "播客内容应包含高级应用和复杂案例，适合进阶学习",
    }
    diff_desc = diff_map.get(difficulty, diff_map["medium"])

    return f"当前修炼境界：{_get_stage_name(stage)}期（第{stage + 1}阶段），内容深度：{level_desc}。{diff_desc}。"


PODCAST_PROMPT = """你是一个专业的教育播客制作人，擅长设计生动的音频节目。根据以下知识内容，生成一份专业的播客脚本。

知识主题：{node_name}
主题描述：{node_description}

参考资料内容：
{source_content}

播客设计要求：
{difficulty_guidance}

严格按照以下 JSON 格式返回（无markdown包裹）：
{{
  "title": "播客主标题",
  "subtitle": "播客副标题",
  "duration_minutes": 20,
  "target_audience": "目标受众描述",
  "episode_summary": "本期节目简介",
  "host": {{
    "name": "主持人名字",
    "persona": "主持人角色设定（如：知识渊博的学者、亲切的导师等）"
  }},
  "segments": [
    {{
      "segment_id": 1,
      "title": "片段标题",
      "duration_seconds": 120,
      "type": "intro",
      "transcript": "完整对话文本",
      "speaker_notes": "演讲提示（语气、节奏、情感等）",
      "sound_effects": ["音效1", "音效2"],
      "background_music": "背景音乐类型"
    }}
  ],
  "key_takeaways": ["核心要点1", "核心要点2", "核心要点3"],
  "resources": ["推荐资源1", "推荐资源2"],
  "next_episode_teaser": "下期节目预告"
}}

播客设计规范：
1. 总时长控制在15-30分钟
2. 片段数量控制在6-12个
3. 每个片段60-300秒
4. 开头片段介绍主题和本期内容
5. 中间片段逐步深入讲解核心概念
6. 使用对话形式，避免单一叙述
7. 适当加入幽默元素，增强趣味性
8. 最后片段进行知识总结和回顾
9. 使用中文撰写
10. 内容必须基于提供的参考资料

片段类型（type）可选：
- intro: 开场介绍
- concept: 概念讲解
- example: 案例分析
- qna: 问答环节
- summary: 总结回顾
- outro: 结束语

语言风格要求：
- 口语化，但保持专业性
- 节奏适中，适合听觉学习
- 关键概念重复强调
- 适当使用比喻和类比
- 避免过于学术化的表述"""


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
    """Validate and normalize podcast script."""
    if not isinstance(script, dict):
        return None

    segments = script.get("segments", [])
    if not isinstance(segments, list) or len(segments) < 4:
        return None

    validated_segments = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        sound_effects = segment.get("sound_effects", [])
        if not isinstance(sound_effects, list):
            sound_effects = []
        validated_segment = {
            "segment_id": segment.get("segment_id", len(validated_segments) + 1),
            "title": str(segment.get("title", "")),
            "duration_seconds": int(segment.get("duration_seconds", 120)),
            "type": str(segment.get("type", "concept")),
            "transcript": str(segment.get("transcript", "")),
            "speaker_notes": str(segment.get("speaker_notes", "")),
            "sound_effects": sound_effects,
            "background_music": str(segment.get("background_music", "")),
        }
        validated_segments.append(validated_segment)

    if len(validated_segments) < 4:
        return None

    return {
        "title": script.get("title", f"{script.get('node_name', '')} - 音频播客"),
        "subtitle": script.get("subtitle", ""),
        "duration_minutes": int(script.get("duration_minutes", 20)),
        "target_audience": script.get("target_audience", ""),
        "episode_summary": script.get("episode_summary", ""),
        "host": script.get("host", {}),
        "segments": validated_segments,
        "key_takeaways": script.get("key_takeaways", []) if isinstance(script.get("key_takeaways"), list) else [],
        "resources": script.get("resources", []) if isinstance(script.get("resources"), list) else [],
        "next_episode_teaser": script.get("next_episode_teaser", ""),
    }


async def generate_podcast(state: PodcastState) -> PodcastState:
    """Generate podcast script from knowledge content."""
    source_content = state["source_content"] or ""
    if len(source_content) > 10000:
        source_content = source_content[:10000] + "\n...(内容已截断)"

    difficulty_guidance = _get_difficulty_guidance(
        state["current_stage"], state["difficulty"]
    )

    prompt = PODCAST_PROMPT.format(
        node_name=state["node_name"],
        node_description=state["node_description"] or "无详细描述",
        source_content=source_content or "无参考资料",
        difficulty_guidance=difficulty_guidance,
    )

    llm = get_llm(temperature=0.5, content_type='podcast')
    try:
        response = await llm.ainvoke([
            SystemMessage(content="你是一个专业的教育播客制作人，只返回 JSON 对象，不要包含任何其他文字。你擅长设计生动的音频节目，包含对话脚本、音效建议和演讲提示。"),
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
                return {**state, "script": None, "error": "生成的脚本格式不合法或片段数量不足"}
        return {**state, "script": None, "error": "LLM 返回内容格式不正确"}
    except Exception as e:
        logger.error("Podcast generation failed: %s", e)
        return {**state, "script": None, "error": str(e)}


def build_podcast_graph() -> StateGraph:
    graph = StateGraph(PodcastState)
    graph.add_node("generate_podcast", generate_podcast)
    graph.set_entry_point("generate_podcast")
    graph.add_edge("generate_podcast", END)
    return graph


podcast_graph = build_podcast_graph().compile()


async def run_podcast_generation(
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
) -> dict | None:
    """Run podcast generation agent and return podcast script."""
    state: PodcastState = {
        "node_name": node_name,
        "node_description": node_description,
        "source_content": source_content,
        "current_stage": current_stage,
        "difficulty": difficulty,
        "script": None,
        "error": None,
    }
    result = await podcast_graph.ainvoke(state)
    return result["script"]
