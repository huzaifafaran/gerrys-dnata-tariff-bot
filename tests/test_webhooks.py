import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import settings
from app.db.models import Base, InboundEvent, OutboxJob, ChatSession
from app.db.session import get_db
from app.api.app import create_app
from app.providers.meta import MetaWhatsAppCloudApiProvider


@pytest.fixture
def webhook_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, TestingSessionLocal


def test_webhook_challenge_success(webhook_client):
    client, _ = webhook_client
    res = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": "123456789",
        },
    )
    assert res.status_code == 200
    assert res.text == "123456789"


def test_webhook_challenge_invalid_token(webhook_client, monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "secret-token-123")
    client, _ = webhook_client
    res = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "123456789",
        },
    )
    assert res.status_code == 403


def test_webhook_signature_validation(monkeypatch, webhook_client):
    secret = "test_meta_app_secret_123"
    monkeypatch.setattr(settings, "WHATSAPP_PROVIDER", "meta")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", secret)

    client, SessionLocal = webhook_client

    body_dict = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "12345", "phone_number_id": "999"},
                    "messages": [{
                        "from": "923001234567",
                        "id": "wamid.HBgLMjA=",
                        "timestamp": "1670000000",
                        "text": {"body": "Hi"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    raw_body = json.dumps(body_dict).encode("utf-8")

    # 1. Invalid signature
    res_bad = client.post(
        "/webhooks/whatsapp",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=invalidhash"}
    )
    assert res_bad.status_code == 401

    # 2. Valid signature
    valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    res_good = client.post(
        "/webhooks/whatsapp",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": valid_sig}
    )
    assert res_good.status_code == 200
    assert res_good.json()["status"] == "accepted"

    # Verify event stored and outbox job created
    with SessionLocal() as db:
        events = db.query(InboundEvent).filter_by(provider_message_id="wamid.HBgLMjA=").all()
        assert len(events) == 1
        jobs = db.query(OutboxJob).filter_by(recipient_id="923001234567").all()
        assert len(jobs) >= 1
        assert "Arrival Date" in jobs[0].payload["text"]


def test_webhook_deduplication(monkeypatch, webhook_client):
    monkeypatch.setattr(settings, "WHATSAPP_PROVIDER", "mock")
    client, SessionLocal = webhook_client

    payload = {"sender_id": "923009999999", "text": "Hi", "message_id": "msg-unique-001"}

    # First delivery
    res1 = client.post("/webhooks/whatsapp", json=payload)
    assert res1.status_code == 200
    assert res1.json()["processed_events"] == 1

    # Duplicate delivery
    res2 = client.post("/webhooks/whatsapp", json=payload)
    assert res2.status_code == 200
    assert res2.json()["processed_events"] == 0

    with SessionLocal() as db:
        events = db.query(InboundEvent).filter_by(provider_message_id="msg-unique-001").all()
        assert len(events) == 1


def test_webhook_status_event_ignored(monkeypatch, webhook_client):
    secret = "status_secret_123"
    monkeypatch.setattr(settings, "WHATSAPP_PROVIDER", "meta")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", secret)
    client, SessionLocal = webhook_client

    # Payload with status receipt only
    status_payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid.123",
                        "status": "delivered",
                        "timestamp": "1670000000",
                        "recipient_id": "923001234567"
                    }]
                }
            }]
        }]
    }
    raw_body = json.dumps(status_payload).encode("utf-8")
    sig = "sha256=" + hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    res = client.post(
        "/webhooks/whatsapp",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig}
    )
    assert res.status_code == 200
    assert "Ignored" in res.json()["message"]

    with SessionLocal() as db:
        jobs = db.query(OutboxJob).all()
        assert len(jobs) == 0
