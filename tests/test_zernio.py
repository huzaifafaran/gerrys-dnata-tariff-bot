import hmac
import hashlib
import json
import pytest
from app.providers.zernio import ZernioWhatsAppProvider
from app.providers.base import OutboundMessage


def test_zernio_parse_webhook():
    provider = ZernioWhatsAppProvider(api_key="zr_test_key", phone_number_id="channel_123")

    # Standard Zernio message.received webhook payload
    payload = {
        "event": "message.received",
        "data": {
            "id": "zr_msg_98765",
            "from": "+923001234567",
            "text": "Hi",
            "type": "text",
        }
    }
    messages = provider.parse_inbound_webhook(payload)
    assert len(messages) == 1
    assert messages[0].sender_id == "+923001234567"
    assert messages[0].text == "Hi"
    assert messages[0].message_id == "zr_msg_98765"


def test_zernio_signature_verification():
    secret = "my_zernio_secret_key"
    provider = ZernioWhatsAppProvider(api_key="zr_test_key", webhook_secret=secret)

    raw_body = json.dumps({"event": "ping"}).encode("utf-8")

    # 1. Direct secret token header
    assert provider.verify_webhook_signature(raw_body, secret) is True
    assert provider.verify_webhook_signature(raw_body, "wrong_secret") is False

    # 2. HMAC SHA-256 header (sha256=...)
    valid_hmac = "sha256=" + hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    assert provider.verify_webhook_signature(raw_body, valid_hmac) is True
    assert provider.verify_webhook_signature(raw_body, "sha256=fake_digest") is False


def test_zernio_send_unconfigured():
    provider = ZernioWhatsAppProvider(api_key="")
    result = provider.send_message(OutboundMessage(recipient_id="923001234567", text="Test"))
    assert result.success is False
    assert "ZERNIO_API_KEY is not configured" in result.error_message
