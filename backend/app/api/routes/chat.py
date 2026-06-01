"""Post-run chat endpoints: send a message, list the conversation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_chat_service
from app.schemas.chat import ChatExchange, ChatMessageRead, SendMessageRequest
from app.services.chat_service import ChatService, RunNotReady

router = APIRouter(prefix="/runs", tags=["chat"])


@router.get("/{run_id}/chat", response_model=list[ChatMessageRead])
async def list_chat(
    run_id: str,
    svc: ChatService = Depends(get_chat_service),
) -> list[ChatMessageRead]:
    return await svc.list_messages(run_id)


@router.post("/{run_id}/chat", response_model=ChatExchange)
async def send_chat(
    run_id: str,
    body: SendMessageRequest,
    svc: ChatService = Depends(get_chat_service),
) -> ChatExchange:
    try:
        return await svc.respond(run_id=run_id, content=body.content, agent=body.agent)
    except RunNotReady as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
