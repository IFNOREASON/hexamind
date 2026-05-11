"""LangGraph Quiz Generation Agent.

Generates stage-difficulty-matched quiz questions based on knowledge node content.
"""

import json
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm
from app.constants import CULTIVATION_STAGES

logger = logging.getLogger(__name__)


class QuizState(TypedDict):
    node_name: str
    node_description: str
    source_content: str
    current_stage: int
    difficulty: str
    questions: list[dict]
    error: str | None


def _get_stage_name(stage: int) -> str:
    if 0 <= stage < len(CULTIVATION_STAGES):
        return CULTIVATION_STAGES[stage]["name"]
    return "凡人"


def _get_difficulty_guidance(stage: int, difficulty: str) -> str:
    if stage <= 2:
        level_desc = "基础记忆和概念理解层面"
    elif stage <= 5:
        level_desc = "理解应用和分析层面，需要综合运用知识"
    elif stage <= 8:
        level_desc = "分析综合和评估层面，需要深度思考"
    else:
        level_desc = "专家评估层面，考察知识的融会贯通"

    diff_map = {
        "easy": "题目应当直白明了，选项区分度高",
        "medium": "题目可以有一定迷惑性，需要仔细思考",
        "hard": "题目需要有陷阱选项和细节考察，增加干扰项难度",
    }
    diff_desc = diff_map.get(difficulty, diff_map["medium"])

    return f"当前修炼境界：{_get_stage_name(stage)}期（第{stage + 1}阶段），考核层面：{level_desc}。{diff_desc}。"


QUIZ_PROMPT = """你是一个智能测验出题系统。根据以下知识内容，生成5道单选题。

知识主题：{node_name}
主题描述：{node_description}

参考资料内容：
{source_content}

出题要求：
{difficulty_guidance}

严格按照以下JSON格式返回（无markdown包裹）：
[
  {{
    "question": "题目内容",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_index": 0
  }}
]

要求：
1. 必须生成恰好5道题目
2. 每道题必须有恰好4个选项
3. correct_index 必须是 0-3 之间的整数
4. 题目内容必须基于提供的参考资料
5. 选项不要出现"以上都是"或"以上都不是"
6. 所有题目和选项必须使用中文"""


def _parse_json_response(content: str) -> list[dict] | None:
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
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    return None


def _validate_questions(questions: list[dict]) -> list[dict]:
    """Validate and normalize quiz questions."""
    valid = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        question = q.get("question", "")
        options = q.get("options", [])
        correct_index = q.get("correct_index", 0)

        if not question or not isinstance(options, list) or len(options) != 4:
            continue
        if not isinstance(correct_index, int) or correct_index < 0 or correct_index > 3:
            correct_index = 0

        valid.append({
            "question": str(question),
            "options": [str(o) for o in options],
            "correct_index": int(correct_index),
        })

    return valid[:5]


async def generate_quiz(state: QuizState) -> QuizState:
    """Generate quiz questions from knowledge content."""
    source_content = state["source_content"] or ""
    if len(source_content) > 8000:
        source_content = source_content[:8000] + "\n...(内容已截断)"

    difficulty_guidance = _get_difficulty_guidance(
        state["current_stage"], state["difficulty"]
    )

    prompt = QUIZ_PROMPT.format(
        node_name=state["node_name"],
        node_description=state["node_description"] or "无详细描述",
        source_content=source_content or "无参考资料",
        difficulty_guidance=difficulty_guidance,
    )

    llm = get_llm(temperature=0.3)
    try:
        response = await llm.ainvoke([
            SystemMessage(content="你是一个专业的测验出题系统，只返回JSON数组，不要包含任何其他文字。"),
            HumanMessage(content=prompt),
        ])
        content = response.content
        if isinstance(content, str):
            parsed = _parse_json_response(content)
            if parsed:
                valid = _validate_questions(parsed)
                if valid:
                    return {**state, "questions": valid, "error": None}
                return {**state, "questions": [], "error": "生成的题目格式不合法"}
        return {**state, "questions": [], "error": "LLM 返回内容不是字符串"}
    except Exception as e:
        logger.error("Quiz generation failed: %s", e)
        return {**state, "questions": [], "error": str(e)}


def build_quiz_graph() -> StateGraph:
    graph = StateGraph(QuizState)
    graph.add_node("generate_quiz", generate_quiz)
    graph.set_entry_point("generate_quiz")
    graph.add_edge("generate_quiz", END)
    return graph


quiz_graph = build_quiz_graph().compile()


async def run_quiz_generation(
    node_name: str,
    node_description: str,
    source_content: str,
    current_stage: int,
    difficulty: str,
) -> list[dict]:
    """Run quiz generation agent and return list of questions."""
    state: QuizState = {
        "node_name": node_name,
        "node_description": node_description,
        "source_content": source_content,
        "current_stage": current_stage,
        "difficulty": difficulty,
        "questions": [],
        "error": None,
    }
    result = await quiz_graph.ainvoke(state)
    return result["questions"]
