"""Background worker for durable outbox message delivery with exponential backoff."""

import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import OutboxJob
from app.providers.base import OutboundMessage, WhatsAppProvider
from app.providers import get_whatsapp_provider

logger = logging.getLogger("outbox_worker")

MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 3


def process_outbox_batch(db: Session, provider: Optional[WhatsAppProvider] = None, limit: int = 20) -> int:
    """Process a batch of pending outbox jobs."""
    if provider is None:
        provider = get_whatsapp_provider()

    now = datetime.now(timezone.utc)
    jobs = (
        db.query(OutboxJob)
        .filter(OutboxJob.status == "pending")
        .filter(OutboxJob.next_retry_at <= now)
        .order_by(OutboxJob.created_at.asc())
        .limit(limit)
        .all()
    )

    processed_count = 0
    for job in jobs:
        processed_count += 1
        payload = job.payload or {}
        outbound = OutboundMessage(
            recipient_id=job.recipient_id,
            text=payload.get("text", ""),
            interactive_type=payload.get("interactive_type"),
            buttons=payload.get("buttons"),
            sections=payload.get("sections"),
        )

        result = provider.send_message(outbound)
        if result.success:
            job.status = "sent"
            job.sent_at = datetime.now(timezone.utc)
            job.last_error = None
            logger.info(f"OutboxJob {job.id} successfully sent to {job.recipient_id}")
        else:
            job.retry_count += 1
            job.last_error = result.error_message
            if result.should_retry and job.retry_count < MAX_RETRIES:
                delay = BASE_BACKOFF_SECONDS * (2 ** (job.retry_count - 1))
                job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                logger.warning(
                    f"OutboxJob {job.id} failed (attempt {job.retry_count}/{MAX_RETRIES}). "
                    f"Retrying in {delay}s. Error: {result.error_message}"
                )
            else:
                job.status = "failed"
                logger.error(f"OutboxJob {job.id} permanently failed: {result.error_message}")

        db.commit()

    return processed_count


def run_worker_loop(poll_interval: float = 1.0, run_once: bool = False):
    """Worker daemon loop."""
    logger.info("Starting Outbox Worker daemon...")
    provider = get_whatsapp_provider()
    while True:
        try:
            with SessionLocal() as db:
                count = process_outbox_batch(db, provider=provider)
        except Exception as e:
            logger.error(f"Worker iteration error: {str(e)}", exc_info=True)

        if run_once:
            break
        time.sleep(poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_worker_loop()
