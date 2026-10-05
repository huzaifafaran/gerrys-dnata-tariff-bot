from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: Literal["development", "production", "test"] = "development"
    APP_TIMEZONE: str = "Asia/Karachi"
    DATABASE_URL: str = "sqlite:///./local_dev.db"
    API_KEY: str = ""
    TARIFF_PROFILE: str = "DEMO_LEGACY"
    ENABLE_DEV_CHAT: bool = True

    # WhatsApp Provider configuration
    WHATSAPP_PROVIDER: Literal["mock", "meta", "zernio", "waha"] = "mock"
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    # Pinned and documented against official Meta WhatsApp Cloud API v21.0
    WHATSAPP_API_VERSION: str = "v21.0"

    # Zernio API configuration (docs.zernio.com)
    ZERNIO_API_KEY: str = ""
    ZERNIO_PHONE_NUMBER_ID: str = ""
    ZERNIO_WEBHOOK_SECRET: str = ""

    # WAHA (devlikeapro/waha open-source WhatsApp API via QR code)
    WAHA_BASE_URL: str = "http://127.0.0.1:3000"
    WAHA_SESSION: str = "default"
    WAHA_API_KEY: str = ""

    # OpenAI Intelligence (GPT-4o-mini NLU & Entity Extractor)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Operational settings
    SESSION_TTL_MINUTES: int = 60
    LOG_RETENTION_DAYS: int = 30
    PUBLIC_BASE_URL: str = ""
    MAX_REQUEST_SIZE_BYTES: int = 1024 * 1024  # 1MB limit for requests

    @property
    def is_dev_chat_allowed(self) -> bool:
        if self.APP_ENV == "production":
            return False
        return self.ENABLE_DEV_CHAT


settings = Settings()
