"""LangGraph PPT Generation Agent.

Generates structured PPT slides based on knowledge node content with RAG retrieval.
"""

import json
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm
from app.constants import CULTIVATION_STAGES

logger = logging.getLogger(__name__)


class PptState(TypedDict):
    node_name: str
    node_description: str
    source_content: str
    current_stage: int
    difficulty: str
    slides: list[dict]
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
        "easy": "PPT内容应简洁明了，重点突出，适合初学者",
        "medium": "PPT内容应包含一定深度，涵盖关键概念和应用",
        "hard": "PPT内容应包含高级应用和复杂案例，适合进阶学习",
    }
    diff_desc = diff_map.get(difficulty, diff_map["medium"])

    return f"当前修炼境界：{_get_stage_name(stage)}期（第{stage + 1}阶段），内容深度：{level_desc}。{diff_desc}。"


PPT_PROMPT = """你是一个专业的 PPT 课件制作专家，擅长设计精美、专业的演示文稿。根据以下知识内容，生成一份高质量的 PPT 课件。

知识主题：{node_name}
主题描述：{node_description}

参考资料内容：
{source_content}

PPT 设计要求：
{difficulty_guidance}

严格按照以下 JSON 格式返回（无markdown包裹）：
{{
  "title": "PPT主标题",
  "theme": {{
    "primary_color": "#3B82F6",
    "secondary_color": "#8B5CF6",
    "accent_color": "#F59E0B",
    "background": "gradient"
  }},
  "slides": [
    {{
      "type": "cover",
      "title": "主标题",
      "subtitle": "副标题/简介",
      "layout": "center",
      "illustration": "插图描述（如：一位学者在图书馆阅读的场景）"
    }},
    {{
      "type": "content",
      "title": "幻灯片标题",
      "content": [
        "要点1：详细描述",
        "要点2：详细描述",
        "要点3：详细描述"
      ],
      "highlights": [0],
      "layout": "two-column",
      "illustration": "插图描述（如：展示代码运行结果的图表）"
    }},
    {{
      "type": "summary",
      "title": "总结",
      "key_points": [
        "核心要点1",
        "核心要点2",
        "核心要点3"
      ],
      "next_steps": "下一步学习建议",
      "layout": "single"
    }}
  ]
}}

幻灯片类型（type）说明：
- cover: 封面页
- content: 内容页（最常用）
- summary: 总结页
- comparison: 对比页
- timeline: 时间轴页
- quote: 引用页
- table: 表格页

布局类型（layout）说明：
- center: 居中布局（适合封面）
- single: 单列布局
- two-column: 双列布局
- three-column: 三列布局
- image-left: 左图右文
- image-right: 左文右图
- full-image: 全图布局

PPT 设计规范：
1. 必须包含 6-10 张幻灯片
2. 第一张幻灯片必须是 cover 类型的封面页
3. 中间幻灯片使用 content、comparison、timeline 等类型展示核心知识点
4. 每张幻灯片聚焦一个主题，内容不要过多
5. 最后一张幻灯片必须是 summary 类型的总结页
6. 使用中文撰写
7. 内容必须基于提供的参考资料

排版设计建议：
- 封面页：大标题居中，配以精美的背景插图
- 内容页：标题突出，要点清晰，重点内容用 highlights 标记（索引数组）
- 对比页：使用两列布局展示对比内容
- 总结页：简洁列出核心要点

插图建议（illustration）：
- 为每张幻灯片提供具体的插图描述
- 插图应与内容相关，增强视觉效果
- 描述要具体，包括场景、人物、物品等
- 封面页必须有插图
- 重要内容页建议添加插图

配色方案（theme）：
- 为整个 PPT 指定统一的配色方案
- primary_color: 主色（用于标题、按钮等）
- secondary_color: 辅助色（用于强调）
- accent_color: 点缀色（用于高亮重点）
- background: 背景类型（gradient/solid/image）

动画建议（在 notes 中描述）：
- 重要要点可以有进入动画
- 强调内容可以有高亮动画
- 过渡效果要专业、简洁"""


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


def _validate_slides(slides: list[dict]) -> list[dict]:
    """Validate and normalize PPT slides."""
    valid = []
    valid_types = {"cover", "content", "summary", "comparison", "timeline", "quote", "table"}
    valid_layouts = {"center", "single", "two-column", "three-column", "image-left", "image-right", "full-image"}

    for slide in slides:
        if not isinstance(slide, dict):
            continue

        slide_type = slide.get("type", "content")
        if slide_type not in valid_types:
            slide_type = "content"

        layout = slide.get("layout", "single")
        if layout not in valid_layouts:
            layout = "single"

        title = slide.get("title", "")
        if not title:
            continue

        normalized = {
            "type": slide_type,
            "title": str(title),
            "layout": layout,
            "content": slide.get("content", "") if isinstance(slide.get("content"), str) else "",
            "content_list": slide.get("content") if isinstance(slide.get("content"), list) else [],
            "highlights": slide.get("highlights", []) if isinstance(slide.get("highlights"), list) else [],
            "key_points": slide.get("key_points", []) if isinstance(slide.get("key_points"), list) else [],
            "next_steps": slide.get("next_steps", "") if isinstance(slide.get("next_steps"), str) else "",
            "subtitle": slide.get("subtitle", "") if isinstance(slide.get("subtitle"), str) else "",
            "illustration": slide.get("illustration", "") if isinstance(slide.get("illustration"), str) else "",
            "notes": slide.get("notes", "") if isinstance(slide.get("notes"), str) else "",
        }

        valid.append(normalized)

    return valid[:15]


def _normalize_theme(theme: dict) -> dict:
    """Normalize theme data with defaults."""
    if not isinstance(theme, dict):
        theme = {}

    return {
        "primary_color": theme.get("primary_color", "#3B82F6"),
        "secondary_color": theme.get("secondary_color", "#8B5CF6"),
        "accent_color": theme.get("accent_color", "#F59E0B"),
        "background": theme.get("background", "gradient"),
    }


async def generate_ppt(state: PptState) -> PptState:
    """Generate PPT slides from knowledge content."""
    source_content = state["source_content"] or ""
    if len(source_content) > 10000:
        source_content = source_content[:10000] + "\n...(内容已截断)"

    difficulty_guidance = _get_difficulty_guidance(
        state["current_stage"], state["difficulty"]
    )

    prompt = PPT_PROMPT.format(
        node_name=state["node_name"],
        node_description=state["node_description"] or "无详细描述",
        source_content=source_content or "无参考资料",
        difficulty_guidance=difficulty_guidance,
    )

    llm = get_llm(temperature=0.2, content_type='ppt')
    try:
        response = await llm.ainvoke([
            SystemMessage(content="你是一个专业的 PPT 课件制作专家，只返回 JSON 对象，不要包含任何其他文字。你擅长设计精美的演示文稿，包含排版建议、插图建议和配色方案。"),
            HumanMessage(content=prompt),
        ])
        content = response.content
        if isinstance(content, str):
            parsed = _parse_json_response(content)
            if parsed and "slides" in parsed and isinstance(parsed["slides"], list):
                slides = _validate_slides(parsed["slides"])
                if len(slides) >= 3:
                    title = parsed.get("title", f"{state['node_name']} - PPT课件")
                    theme = _normalize_theme(parsed.get("theme", {}))
                    return {
                        **state,
                        "slides": [
                            {**s, "ppt_title": title, "theme": theme}
                            for s in slides
                        ],
                        "error": None
                    }
                return {**state, "slides": [], "error": "生成的幻灯片数量不足或格式不合法"}
        return {**state, "slides": [], "error": "LLM 返回内容格式不正确"}
    except Exception as e:
        logger.error("PPT generation failed: %s", e)
        return {**state, "slides": [], "error": str(e)}


def build_ppt_graph() -> StateGraph:
    graph = StateGraph(PptState)
    graph.add_node("generate_ppt", generate_ppt)
    graph.set_entry_point("generate_ppt")
    graph.add_edge("generate_ppt", END)
    return graph


ppt_graph = build_ppt_graph().compile()


async def run_ppt_generation(
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
) -> list[dict]:
    """Run PPT generation agent and return list of slides."""
    state: PptState = {
        "node_name": node_name,
        "node_description": node_description,
        "source_content": source_content,
        "current_stage": current_stage,
        "difficulty": difficulty,
        "slides": [],
        "error": None,
    }
    result = await ppt_graph.ainvoke(state)
    return result["slides"]
