import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import ChatRequest
from app.services.retrieval import retrieve_context
from app.agents.chat_agent import run_chat_stream

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Simple in-memory chat history (per-session; production should use checkpointer)
_chat_history: list[dict] = []


@router.post("")
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    """SSE streaming chat endpoint powered by LangGraph chat agent."""

    # Step 1: Retrieve knowledge context (RAG)
    context = await retrieve_context(body.message, db)

    # Step 2: Stream response from chat agent
    async def generate():
        full_response = ""
        try:
            async for chunk in run_chat_stream(
                user_message=body.message,
                knowledge_context=context,
                chat_history=_chat_history,
            ):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_msg = "抱歉，处理请求时出现错误。"
            yield f"data: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"
            full_response = error_msg

        # Save to history (memory)
        _chat_history.append({"role": "user", "content": body.message})
        _chat_history.append({"role": "assistant", "content": full_response})

        # Keep history manageable
        if len(_chat_history) > 40:
            _chat_history[:] = _chat_history[-40:]

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
