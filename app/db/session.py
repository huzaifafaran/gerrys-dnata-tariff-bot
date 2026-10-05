"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables and seed initial data."""
    from app.db.models import Base
    from app.db.seed import seed_database
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)

