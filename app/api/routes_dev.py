"""Development-only chat endpoints and simulator (strictly disabled in production)."""

import os
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.conversation.state_machine import ConversationEngine

router = APIRouter(tags=["Development Only"])

SIMULATOR_HTML_PATH = os.path.join(os.path.dirname(__file__), "simulator.html")


def check_dev_allowed():
    if not settings.is_dev_chat_allowed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development endpoints are disabled in this environment.",
        )


class DevChatRequest(BaseModel):
    session_id: str = "dev-tester-01"
    message: str


class DevChatResponse(BaseModel):
    session_id: str
    reply: str
    current_state: str
    collected_data: dict


@router.post("/dev/chat", response_model=DevChatResponse, dependencies=[Depends(check_dev_allowed)])
def dev_chat(payload: DevChatRequest, db: Session = Depends(get_db)):
    """Simulate conversation synchronously without WhatsApp webhook infrastructure."""
    engine = ConversationEngine(db)
    reply = engine.process_message(payload.session_id, payload.message)
    sess, _ = engine.get_or_create_session(payload.session_id)
    return DevChatResponse(
        session_id=payload.session_id,
        reply=reply,
        current_state=sess.current_state,
        collected_data=sess.collected_data or {},
    )


@router.get("/dev/simulator", response_class=HTMLResponse, dependencies=[Depends(check_dev_allowed)])
@router.get("/simulator", response_class=HTMLResponse, dependencies=[Depends(check_dev_allowed)])
@router.get("/", response_class=HTMLResponse, dependencies=[Depends(check_dev_allowed)])
def get_simulator():
    """Rich WhatsApp Web Chatbot Simulator for testing."""
    if os.path.exists(SIMULATOR_HTML_PATH):
        with open(SIMULATOR_HTML_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Simulator HTML template not found.</h1>"
