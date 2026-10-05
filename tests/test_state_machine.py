from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.conversation.state_machine import ConversationEngine
from app.conversation.parser import parse_date_input


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


def test_date_parser_ambiguity():
    # Ambiguous: 02/03/2026
    dt, err = parse_date_input("02/03/2026")
    assert dt is None
    assert "ambiguous" in err.lower()

    # Unambiguous DD/MM/YYYY: 25/09/2026
    dt, err = parse_date_input("25/09/2026")
    assert err is None
    assert dt.isoformat() == "2026-09-25"

    # Unambiguous ISO: 2026-10-01
    dt, err = parse_date_input("2026-10-01")
    assert err is None
    assert dt.isoformat() == "2026-10-01"

    # Textual month: 01-Oct-2026
    dt, err = parse_date_input("01-Oct-2026")
    assert err is None
    assert dt.isoformat() == "2026-10-01"


def test_full_conversation_flow(db_session):
    engine = ConversationEngine(db_session)
    phone = "whatsapp:+923001234567"

    # 1. Start
    res1 = engine.process_message(phone, "Hello")
    assert "Cargo Arrival Date" in res1

    # 2. Arrival Date
    res2 = engine.process_message(phone, "2026-10-01")
    assert "Cargo Payment Date" in res2

    # 3. Payment Date
    res3 = engine.process_message(phone, "2026-10-01")
    assert "Cargo Category" in res3

    # 4. Category AFU
    res4 = engine.process_message(phone, "1")
    assert "Cargo Class" in res4
    assert "GEN" in res4

    # 5. Cargo Class GEN
    res5 = engine.process_message(phone, "1")
    assert "Gross Cargo Weight" in res5

    # 6. Weight 1000 kg
    res6 = engine.process_message(phone, "1000")
    assert "Delivery Station" in res6

    # 7. Station KHI
    res7 = engine.process_message(phone, "1")
    assert "Oversize" in res7

    # 8. Oversize Yes
    res8 = engine.process_message(phone, "1")
    assert "Review Shipment Details" in res8
    assert "1000 kg" in res8
    assert "Yes" in res8

    # 9. Confirm
    res9 = engine.process_message(phone, "CONFIRM")
    assert "TARIFF QUOTATION" in res9
    assert "131,431" in res9
    assert "Official Gerry’s/dnata Tariff Quotation" in res9


def test_review_and_edit_field(db_session):
    engine = ConversationEngine(db_session)
    phone = "whatsapp:+923009998888"

    # Run up to review
    engine.process_message(phone, "hi")
    engine.process_message(phone, "2026-10-01")
    engine.process_message(phone, "2026-10-01")
    engine.process_message(phone, "AFU")
    engine.process_message(phone, "GEN")
    engine.process_message(phone, "1000")
    engine.process_message(phone, "KHI")
    engine.process_message(phone, "Yes")

    # Now edit oversize to No
    edit_resp = engine.process_message(phone, "edit oversize")
    assert "Is this consignment" in edit_resp
    assert "Oversize" in edit_resp

    update_resp = engine.process_message(phone, "No")
    assert "Review Shipment Details" in update_resp
    assert "Oversize:* `No`" in update_resp

    # Confirm -> should yield 84,012 PKR
    calc_resp = engine.process_message(phone, "CONFIRM")
    assert "84,012" in calc_resp


def test_invalid_date_ordering_rejected(db_session):
    engine = ConversationEngine(db_session)
    phone = "whatsapp:+923001112222"

    engine.process_message(phone, "hi")
    engine.process_message(phone, "2026-10-05")
    # Attempt payment date earlier than arrival date
    err_resp = engine.process_message(phone, "2026-10-01")
    assert "cannot be earlier than arrival date" in err_resp


def test_session_isolation(db_session):
    engine = ConversationEngine(db_session)
    user_a = "whatsapp:+923001111111"
    user_b = "whatsapp:+923002222222"

    engine.process_message(user_a, "hi")
    engine.process_message(user_a, "2026-10-01")

    engine.process_message(user_b, "hi")
    # user_b is at arrival date, user_a is at payment date
    sess_a, _ = engine.get_or_create_session(user_a)
    sess_b, _ = engine.get_or_create_session(user_b)
    assert sess_a.current_state == "AWAITING_PAYMENT_DATE"
    assert sess_b.current_state == "AWAITING_ARRIVAL_DATE"


def test_session_expiration(db_session):
    engine = ConversationEngine(db_session)
    user = "whatsapp:+923003333333"

    engine.process_message(user, "hi")
    sess, _ = engine.get_or_create_session(user)
    # Manually expire session
    sess.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    resp = engine.process_message(user, "2026-10-01")
    assert "expired due to inactivity" in resp
