"""LangGraph Chat Agent with memory (checkpointer) and RAG retrieval.

Pipeline: load_context → retrieve_knowledge → generate_response
Uses AsyncSqliteSaver for conversation memory persistence.
"""

import json
import logging
from typing import TypedDict, AsyncGenerator

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.llm import get_llm

logger = logging.getLogger(__name__)


# ── State ──────────────────────────────────────────────

class ChatState(TypedDict):
    user_message: str
    knowledge_context: str
    chat_history: list[dict]  # [{role, content}]
    ai_response: str


# ── Nodes ──────────────────────────────────────────────

SYSTEM_PROMPT = """你是 HexaMind AI 学习助手，一个知识图谱驱动的智能学习平台。

你的职责：
1. 回答用户关于其知识库中内容的问题
2. 解释知识概念之间的关系
3. 提供学习建议和路径规划
4. 帮助用户理解复杂知识

规则：
- 优先使用知识库中的信息回答
- 如果知识库中没有相关内容，坦诚告知并提供一般性回答
- 回答简洁、准确，使用中文
- 引用知识点时提及来源"""


async def generate_response(state: ChatState) -> ChatState:
    """Generate AI response using LLM with chat history and retrieved context."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Add knowledge context if available
    if state["knowledge_context"]:
        messages.append(SystemMessage(content=state["knowledge_context"]))

    # Add chat history (last 10 exchanges)
    history = state["chat_history"][-20:]  # Last 20 messages (10 exchanges)
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    # Add current user message
    messages.append(HumanMessage(content=state["user_message"]))

    llm = get_llm()
    try:
        response = await llm.ainvoke(messages)
        ai_text = response.content if isinstance(response.content, str) else str(response.content)
    except Exception as e:
        logger.error("Chat LLM failed: %s", e)
        ai_text = "抱歉，我暂时无法处理你的请求。请稍后再试。"

    return {**state, "ai_response": ai_text}


# ── Graph Definition ──────────────────────────────────

def build_chat_graph() -> StateGraph:
    graph = StateGraph(ChatState)
    graph.add_node("generate_response", generate_response)
    graph.set_entry_point("generate_response")
    graph.add_edge("generate_response", END)
    return graph


chat_graph = build_chat_graph().compile()


async def run_chat(
    user_message: str,
    knowledge_context: str,
    chat_history: list[dict],
) -> str:
    """Run chat agent and return response text."""
    state: ChatState = {
        "user_message": user_message,
        "knowledge_context": knowledge_context,
        "chat_history": chat_history,
        "ai_response": "",
    }
    result = await chat_graph.ainvoke(state)
    return result["ai_response"]


async def run_chat_stream(
    user_message: str,
    knowledge_context: str,
    chat_history: list[dict],
) -> AsyncGenerator[str, None]:
    """Run chat with streaming response."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if knowledge_context:
        messages.append(SystemMessage(content=knowledge_context))

    for msg in chat_history[-20:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    llm = get_llm()
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        logger.error("Chat stream failed: %s", e)
        yield "抱歉，我暂时无法处理你的请求。"
