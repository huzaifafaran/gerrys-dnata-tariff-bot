from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.models import Base
from app.db.session import get_db
from app.api.app import create_app


from sqlalchemy.pool import StaticPool

@pytest.fixture
def test_client():
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
        yield client


def test_health_live(test_client):
    res = test_client.get("/health/live")
    assert res.status_code == 200
    assert res.json() == {"status": "live"}


def test_health_ready(test_client):
    res = test_client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    # Ensure no secrets in output
    for key in ["password", "secret", "token", "key"]:
        assert key not in str(data).lower()


def test_catalog_endpoint(test_client):
    res = test_client.get("/api/v1/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "supported_categories" in data
    assert "AFU" in data["supported_categories"]
    assert "KHI" in data["stations"]


def test_calculation_api_valid_request(test_client):
    # Matches contracts/calculation-request.json
    payload = {
        "arrival_date": "2026-10-01",
        "payment_date": "2026-10-01",
        "category": "AFU",
        "cargo_class": "GEN",
        "weight_kg": "1000",
        "station": "KHI",
        "is_oversize": True
    }
    res = test_client.post("/api/v1/calculations", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "calculated"
    assert data["grand_total_pkr"] == "131431"
    assert data["subtotal_pkr"] == "114288"
    assert data["tax_pkr"] == "17143"
    assert data["policy_profile"] == "DEMO_LEGACY"


def test_calculation_api_oversize_false(test_client):
    payload = {
        "arrival_date": "2026-10-01",
        "payment_date": "2026-10-01",
        "category": "AFU",
        "cargo_class": "GEN",
        "weight_kg": "1000",
        "station": "KHI",
        "is_oversize": False
    }
    res = test_client.post("/api/v1/calculations", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "calculated"
    assert data["grand_total_pkr"] == "84012"


def test_calculation_api_unsupported_path(test_client):
    payload = {
        "arrival_date": "2026-10-01",
        "payment_date": "2026-10-02",
        "category": "ICG",
        "cargo_class": "IGEN",
        "weight_kg": "100",
        "station": "KHI",
        "is_oversize": False
    }
    res = test_client.post("/api/v1/calculations", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "calculated"
    assert data["grand_total_pkr"] is not None


def test_dev_chat_enabled_in_development(test_client):
    res = test_client.post("/dev/chat", json={"session_id": "test-dev-1", "message": "Hi"})
    assert res.status_code == 200
    data = res.json()
    assert "Cargo Arrival Date" in data["reply"]


def test_dev_chat_disabled_in_production(monkeypatch, test_client):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    res = test_client.post("/dev/chat", json={"session_id": "test-dev-2", "message": "Hi"})
    assert res.status_code == 404
