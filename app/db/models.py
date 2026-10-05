"""SQLAlchemy database models for sessions, events, outbox jobs, calculations, and tariffs."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(128), primary_key=True)
    current_state = Column(String(64), nullable=False, default="START")
    collected_data = Column(JSON, nullable=False, default=dict)
    last_active_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_chat_sessions_expires_at", "expires_at"),
    )


class InboundEvent(Base):
    __tablename__ = "inbound_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_message_id = Column(String(256), nullable=False, unique=True, index=True)
    sender_id = Column(String(128), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class OutboxJob(Base):
    __tablename__ = "outbox_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_id = Column(String(128), nullable=False, index=True)
    message_type = Column(String(32), nullable=False, default="text")
    payload = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default="pending", index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    sent_at = Column(DateTime(timezone=True), nullable=True)


class CalculationRecord(Base):
    __tablename__ = "calculation_records"

    calculation_id = Column(String(64), primary_key=True)
    session_id = Column(String(128), nullable=True, index=True)
    inputs = Column(JSON, nullable=False)
    breakdown = Column(JSON, nullable=False)
    subtotal_pkr = Column(String(64), nullable=True)
    tax_pkr = Column(String(64), nullable=True)
    grand_total_pkr = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False)
    policy_profile = Column(String(32), nullable=False)
    tariff_version = Column(String(64), nullable=True)
    issues = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class TariffVersionRecord(Base):
    __tablename__ = "tariff_versions"

    version_code = Column(String(64), primary_key=True)
    profile = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)  # "active", "provisional", "approved", "deprecated"
    description = Column(Text, nullable=False)
    rules_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
