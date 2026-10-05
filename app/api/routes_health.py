"""Health and readiness check endpoints."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
def liveness():
    """Simple liveness probe."""
    return {"status": "live"}


@router.get("/ready")
def readiness(response: Response, db: Session = Depends(get_db)):
    """Readiness probe checking database connectivity and configuration.

    Never reveals secrets, passwords, or tokens.
    """
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "reason": "Database connection unavailable",
        }

    return {
        "status": "ready",
        "database": "connected",
        "tariff_profile": settings.TARIFF_PROFILE,
        "whatsapp_provider": settings.WHATSAPP_PROVIDER,
        "environment": settings.APP_ENV,
    }
