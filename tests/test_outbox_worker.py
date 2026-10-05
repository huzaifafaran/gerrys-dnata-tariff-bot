from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, OutboxJob
from app.providers.mock import MockWhatsAppProvider
from app.worker.outbox_worker import process_outbox_batch, MAX_RETRIES


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_outbox_worker_successful_send(db_session):
    provider = MockWhatsAppProvider()

    job = OutboxJob(
        recipient_id="923001234567",
        message_type="text",
        payload={"text": "Hello test message"},
        status="pending",
        retry_count=0,
        next_retry_at=datetime.now(timezone.utc) - timedelta(seconds=10),
    )
    db_session.add(job)
    db_session.commit()

    count = process_outbox_batch(db_session, provider=provider)
    assert count == 1
    assert len(provider.sent_messages) == 1
    assert provider.sent_messages[0].text == "Hello test message"

    db_session.refresh(job)
    assert job.status == "sent"
    assert job.sent_at is not None
    assert job.last_error is None


def test_outbox_worker_retry_backoff(db_session):
    provider = MockWhatsAppProvider()
    provider.should_fail_send = True
    provider.fail_should_retry = True

    job = OutboxJob(
        recipient_id="923001234567",
        message_type="text",
        payload={"text": "Fail test message"},
        status="pending",
        retry_count=0,
        next_retry_at=datetime.now(timezone.utc) - timedelta(seconds=10),
    )
    db_session.add(job)
    db_session.commit()

    count = process_outbox_batch(db_session, provider=provider)
    assert count == 1

    db_session.refresh(job)
    assert job.status == "pending"
    assert job.retry_count == 1
    assert job.last_error == "Mock provider simulated send failure"
    next_dt = job.next_retry_at if job.next_retry_at.tzinfo else job.next_retry_at.replace(tzinfo=timezone.utc)
    assert next_dt > datetime.now(timezone.utc)


def test_outbox_worker_permanent_failure_after_max_retries(db_session):
    provider = MockWhatsAppProvider()
    provider.should_fail_send = True
    provider.fail_should_retry = True

    job = OutboxJob(
        recipient_id="923001234567",
        message_type="text",
        payload={"text": "Permanent fail message"},
        status="pending",
        retry_count=MAX_RETRIES - 1,
        next_retry_at=datetime.now(timezone.utc) - timedelta(seconds=10),
    )
    db_session.add(job)
    db_session.commit()

    count = process_outbox_batch(db_session, provider=provider)
    assert count == 1

    db_session.refresh(job)
    assert job.status == "failed"
    assert job.retry_count == MAX_RETRIES
