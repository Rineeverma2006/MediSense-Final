"""AI assistant chat with conversation history persisted per user."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db, log_action
from app.core.config import AI_MAX_HISTORY
from app.database.models import Conversation, Message, User
from app.services import ai_service

router = APIRouter(tags=["assistant"])


def _conversation(s: Session, conversation_id: int, user: User) -> Conversation:
    row = s.query(Conversation).filter_by(id=conversation_id, user_id=user.id).first()
    if not row:
        raise HTTPException(404, "Conversation not found")
    return row


def _title(text: str) -> str:
    cleaned = " ".join(text.split())
    return (cleaned[:60] + "…") if len(cleaned) > 60 else (cleaned or "New Conversation")


def _history(conversation: Conversation) -> list[dict]:
    messages = conversation.messages[-AI_MAX_HISTORY:]
    return [{"role": m.role, "content": m.content} for m in messages]


def _summary(conversation: Conversation) -> dict:
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "message_count": len(conversation.messages),
    }


@router.get("/api/assistant/availability")
def availability():
    return ai_service.availability()


@router.post("/api/assistant")
def ask(
    body: schemas.AskIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    if body.conversation_id:
        conversation = _conversation(s, body.conversation_id, user)
    else:
        conversation = Conversation(user_id=user.id, title=_title(body.message))
        s.add(conversation)
        s.commit()
        s.refresh(conversation)

    history = _history(conversation)
    result = ai_service.reply(body.message, history)

    s.add(Message(conversation_id=conversation.id, role="user", content=body.message))
    s.add(
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.get("answer", ""),
        )
    )
    conversation.updated_at = datetime.utcnow()
    s.commit()
    log_action(s, user.id, "assistant_message", commit=False)

    return {
        **result,
        "conversation_id": conversation.id,
        "conversation_title": conversation.title,
    }


@router.get("/api/assistant/conversations")
def list_conversations(
    user: User = Depends(current_user), s: Session = Depends(db)
):
    rows = (
        s.query(Conversation)
        .filter_by(user_id=user.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .all()
    )
    return [_summary(c) for c in rows]


@router.post("/api/assistant/conversations")
def create_conversation(
    body: schemas.ConversationIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    conversation = Conversation(user_id=user.id, title=body.title[:255] or "New Conversation")
    s.add(conversation)
    s.commit()
    s.refresh(conversation)
    return _summary(conversation)


@router.get("/api/assistant/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    conversation = _conversation(s, conversation_id, user)
    return {
        **_summary(conversation),
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content,
             "created_at": m.created_at.isoformat()}
            for m in conversation.messages
        ],
    }


@router.delete("/api/assistant/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    conversation = _conversation(s, conversation_id, user)
    s.delete(conversation)
    s.commit()
    log_action(s, user.id, f"conversation_deleted:{conversation_id}")
    return {"status": "deleted", "id": conversation_id}
