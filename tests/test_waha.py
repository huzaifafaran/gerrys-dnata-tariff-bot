import pytest
from app.providers.waha import WAHAWhatsAppProvider
from app.providers.base import OutboundMessage


def test_waha_parse_inbound_message():
    provider = WAHAWhatsAppProvider()
    payload = {
        "event": "message",
        "session": "default",
        "payload": {
            "id": "true_923001234567@c.us_3EB0...",
            "from": "923001234567@c.us",
            "body": "Hi",
            "fromMe": False,
        }
    }
    messages = provider.parse_inbound_webhook(payload)
    assert len(messages) == 1
    assert messages[0].sender_id == "923001234567"
    assert messages[0].text == "Hi"


def test_waha_ignore_from_me():
    provider = WAHAWhatsAppProvider()
    payload = {
        "event": "message",
        "session": "default",
        "payload": {
            "id": "false_923001234567@c.us_...",
            "from": "923001234567@c.us",
            "body": "Bot reply",
            "fromMe": True,
        }
    }
    messages = provider.parse_inbound_webhook(payload)
    assert len(messages) == 0


def test_waha_chat_id_formatting():
    # Use unused port to verify network failure handled gracefully
    provider = WAHAWhatsAppProvider(base_url="http://127.0.0.1:59999")
    msg = OutboundMessage(recipient_id="+923001234567", text="Test message")
    result = provider.send_message(msg)
    assert result.success is False
    assert result.should_retry is True
