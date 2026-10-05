"""Main FastAPI Application factory and middleware configuration."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import engine, SessionLocal
from app.db.models import Base
from app.db.seed import seed_database
from app.api.routes_health import router as health_router
from app.api.routes_calculator import router as calculator_router
from app.api.routes_webhook import router as webhook_router
from app.api.routes_dev import router as dev_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tariff_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables exist and seed default tariff versions
    logger.info("Initializing database tables and seed data...")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    logger.info("Application ready.")
    yield
    # Shutdown
    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gerry’s / dnata Tariff Calculator WhatsApp Chatbot POC",
        description="Deterministic air cargo tariff calculator with Meta WhatsApp Cloud API integration.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration: strict in production, configurable for internal development
    if settings.APP_ENV == "production":
        origins = [settings.PUBLIC_BASE_URL] if settings.PUBLIC_BASE_URL else []
    else:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request size limiter middleware
    @app.middleware("http")
    async def limit_request_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > settings.MAX_REQUEST_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Payload exceeds maximum permitted size",
                    )
            except ValueError:
                pass
        return await call_next(request)

    # Mount routers
    app.include_router(health_router)
    app.include_router(calculator_router)
    app.include_router(webhook_router)
    app.include_router(dev_router)

    @app.get("/pairing-code")
    async def pairing_code_status():
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.WAHA_BASE_URL}/api/pairingCode", timeout=3.0)
                data = resp.json()
                code = data.get("pairingCode")
                if code:
                    return {
                        "status": "ready_to_pair",
                        "phone": data.get("phone"),
                        "pairing_code": code,
                        "instruction": f"Open WhatsApp on {data.get('phone')} -> Linked Devices -> Link a Device -> Link with phone number instead -> Enter: {code}"
                    }
                return data
        except Exception as e:
            return {"status": "starting", "message": "WhatsApp bridge is initializing. Refresh this page in a few seconds.", "error": str(e)}

    return app


app = create_app()
