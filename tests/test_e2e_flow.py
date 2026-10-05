import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import settings
from app.db.models import Base, OutboxJob, CalculationRecord
from app.db.session import get_db
from app.api.app import create_app
from app.providers import get_whatsapp_provider
from app.providers.mock import MockWhatsAppProvider
from app.worker.outbox_worker import process_outbox_batch


@pytest.fixture
def e2e_setup():
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

    mock_provider = MockWhatsAppProvider()

    with TestClient(app) as client:
        yield client, TestingSessionLocal, mock_provider


def test_full_roundtrip_simulated_whatsapp_oversize_yes(e2e_setup, monkeypatch):
    client, SessionLocal, mock_provider = e2e_setup
    monkeypatch.setattr("app.api.routes_webhook.get_whatsapp_provider", lambda: mock_provider)
    monkeypatch.setattr("app.worker.outbox_worker.get_whatsapp_provider", lambda: mock_provider)

    phone = "923001234567"

    conversation_steps = [
        ("Hi", "Cargo Arrival Date"),
        ("2026-10-01", "Cargo Payment Date"),
        ("2026-10-01", "Cargo Category"),
        ("1", "Cargo Class"),  # AFU
        ("1", "Gross Cargo Weight"),  # GEN
        ("1000", "Delivery Station"),
        ("1", "Oversize"),  # KHI
        ("1", "Review Shipment Details"),  # Oversize Yes
        ("CONFIRM", "TARIFF QUOTATION"),
    ]

    for idx, (user_text, expected_in_reply) in enumerate(conversation_steps):
        payload = {
            "sender_id": phone,
            "text": user_text,
            "message_id": f"msg-e2e-{idx+1}"
        }
        res = client.post("/webhooks/whatsapp", json=payload)
        assert res.status_code == 200

        # Execute outbox worker batch to deliver outbound job
        with SessionLocal() as db:
            process_outbox_batch(db, provider=mock_provider)

        # Check last message sent by mock provider
        assert len(mock_provider.sent_messages) > 0
        last_outbound = mock_provider.sent_messages[-1]
        assert last_outbound.recipient_id == phone
        assert expected_in_reply in last_outbound.text

    # Final result checks for Oversize Yes (Fixture 1 from DECISIONS.md)
    final_text = mock_provider.sent_messages[-1].text
    assert "131,431" in final_text
    assert "114,288" in final_text  # Subtotal
    assert "17,143" in final_text   # Tax
    assert "Official Gerry’s/dnata Tariff Quotation" in final_text

    # Verify calculation recorded in database
    with SessionLocal() as db:
        calcs = db.query(CalculationRecord).all()
        assert len(calcs) == 1
        assert calcs[0].grand_total_pkr == "131431"
        assert calcs[0].status == "calculated"


def test_full_roundtrip_simulated_whatsapp_oversize_no(e2e_setup, monkeypatch):
    client, SessionLocal, mock_provider = e2e_setup
    monkeypatch.setattr("app.api.routes_webhook.get_whatsapp_provider", lambda: mock_provider)
    monkeypatch.setattr("app.worker.outbox_worker.get_whatsapp_provider", lambda: mock_provider)

    phone = "923007654321"

    conversation_steps = [
        ("Hi", "Cargo Arrival Date"),
        ("2026-10-01", "Cargo Payment Date"),
        ("2026-10-01", "Cargo Category"),
        ("1", "Cargo Class"),  # AFU
        ("1", "Gross Cargo Weight"),  # GEN
        ("1000", "Delivery Station"),
        ("1", "Oversize"),  # KHI
        ("2", "Review Shipment Details"),  # Oversize No
        ("CONFIRM", "TARIFF QUOTATION"),
    ]

    for idx, (user_text, _) in enumerate(conversation_steps):
        payload = {
            "sender_id": phone,
            "text": user_text,
            "message_id": f"msg-e2e-no-{idx+1}"
        }
        res = client.post("/webhooks/whatsapp", json=payload)
        assert res.status_code == 200

        with SessionLocal() as db:
            process_outbox_batch(db, provider=mock_provider)

    final_text = mock_provider.sent_messages[-1].text
    assert "84,012" in final_text
    assert "73,054" in final_text  # Subtotal
    assert "10,958" in final_text  # Tax
