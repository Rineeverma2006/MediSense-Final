"""Voice assistant support.

Speech recognition and synthesis run **in the browser** using the Web Speech API —
audio never leaves the device and no audio is stored server-side. This router only
exposes the capability manifest and a convenience endpoint that returns a
speak-ready assistant answer.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db
from app.database.models import Conversation, Message, User
from app.services import ai_service

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.get("/config")
def voice_config():
    """Capabilities the frontend should enable/disable.

    ``server_tts`` is false by design: synthesis happens in the browser so no audio
    is uploaded and no TTS vendor key is required.
    """
    return {
        "recognition": "browser_web_speech_api",
        "synthesis": "browser_speech_synthesis",
        "server_tts": False,
        "languages": [
            {"code": "en-US", "label": "English (US)"},
            {"code": "en-GB", "label": "English (UK)"},
            {"code": "en-IN", "label": "English (India)"},
            {"code": "hi-IN", "label": "Hindi"},
            {"code": "es-ES", "label": "Spanish"},
            {"code": "fr-FR", "label": "French"},
        ],
        "notes": (
            "Speech recognition and synthesis use the browser Web Speech API. "
            "Audio is processed on-device and is not uploaded or stored. "
            "Browsers without Web Speech support will only offer text chat."
        ),
        "privacy": "no_audio_upload",
    }


@router.post("/ask")
def voice_ask(
    body: schemas.AskIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    """Same reasoning as ``/api/assistant`` but returns speech-friendly metadata."""
    status = ai_service.availability()
    if body.conversation_id:
        conversation = (
            s.query(Conversation)
            .filter_by(id=body.conversation_id, user_id=user.id)
            .first()
        )
        if not conversation:
            conversation = Conversation(user_id=user.id, title=body.message[:60])
            s.add(conversation)
            s.commit()
            s.refresh(conversation)
    else:
        conversation = Conversation(user_id=user.id, title=body.message[:60] or "Voice chat")
        s.add(conversation)
        s.commit()
        s.refresh(conversation)

    history = [
        {"role": m.role, "content": m.content} for m in conversation.messages[-8:]
    ]
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

    # Strip markdown emphasis so text-to-speech does not read symbols aloud.
    spoken = (
        result.get("answer", "")
        .replace("**", "")
        .replace("*", "")
        .replace("#", "")
        .replace("`", "")
    )
    return {
        **result,
        "conversation_id": conversation.id,
        "speech": {"text": spoken, "lang": "en-US"},
        "mode": status["mode"],
    }
