from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import FRIENDLY_ERROR_MESSAGE, GeminiServiceError, gemini_service

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Meneruskan pesan chatbot ke service Gemini tanpa memaparkan detail error provider."""
    try:
        reply = await run_in_threadpool(gemini_service.reply, payload.message.strip(), payload.conversation_id)
        return ChatResponse(reply=reply)
    except GeminiServiceError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=FRIENDLY_ERROR_MESSAGE)
