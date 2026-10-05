"""Webhook endpoints for Meta WhatsApp Cloud API and mock provider."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.db.models import InboundEvent, OutboxJob
from app.providers import get_whatsapp_provider
from app.conversation.state_machine import ConversationEngine
from app.worker.outbox_worker import process_outbox_batch

logger = logging.getLogger("webhook_routes")
router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp Webhook"])


@router.get("", status_code=status.HTTP_200_OK)
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """Meta WhatsApp Cloud API Webhook Subscription Verification."""
    if hub_mode == "subscribe":
        if hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN or not settings.WHATSAPP_VERIFY_TOKEN:
            # Return challenge as raw text or integer
            return Response(content=str(hub_challenge or ""), media_type="text/plain")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hub.mode")


@router.post("", status_code=status.HTTP_200_OK)
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Receive inbound events with HMAC signature validation and outbox persistence."""
    provider = get_whatsapp_provider()
    raw_body = await request.body()
    signature_header = (
        request.headers.get("X-Hub-Signature-256")
        or request.headers.get("X-Zernio-Signature")
        or request.headers.get("X-Webhook-Secret")
        or request.headers.get("Authorization")
    )

    # Verify signature
    if not provider.verify_webhook_signature(raw_body, signature_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook signature",
        )

    try:
        payload = json.loads(raw_body)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from e

    inbound_msgs = provider.parse_inbound_webhook(payload)
    if not inbound_msgs:
        # Status receipt (delivered/read/sent) or ping event safely acknowledged
        return {"status": "ok", "message": "Ignored non-message or status event"}

    engine = ConversationEngine(db)
    processed = 0

    for msg in inbound_msgs:
        # Message Deduplication
        existing = db.query(InboundEvent).filter_by(provider_message_id=msg.message_id).first()
        if existing:
            logger.info(f"Duplicate message_id '{msg.message_id}' discarded safely.")
            continue

        # Record inbound event
        event_record = InboundEvent(
            provider_message_id=msg.message_id,
            sender_id=msg.sender_id,
            payload=msg.raw_payload,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event_record)

        # Process conversation state
        reply_text = engine.process_message(msg.sender_id, msg.text)

        # Enqueue Outbound Job (Outbox Pattern)
        outbox_job = OutboxJob(
            recipient_id=msg.sender_id,
            message_type="text",
            payload={"text": reply_text},
            status="pending",
            retry_count=0,
            next_retry_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        db.add(outbox_job)
        processed += 1

    # Atomically commit inbound event, session state, and outbox job
    db.commit()

    # In mock provider mode (e.g. tests or dev simulator), process outbox immediately for rapid round-trip
    if settings.WHATSAPP_PROVIDER == "mock":
        process_outbox_batch(db, provider=provider)

    return {"status": "accepted", "processed_events": processed}
