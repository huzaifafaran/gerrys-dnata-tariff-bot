"""WAHA (WhatsApp HTTP API - devlikeapro/waha) Provider Adapter.

Open-source WhatsApp API running locally via Docker.
- Zero Meta accounts or business verification needed
- Direct QR code scan via Linked Devices
- Endpoints: POST /api/sendText
- Webhook event: "message"
"""

import logging
from typing import List, Optional, Dict, Any
import httpx
from app.config import settings
from app.providers.base import WhatsAppProvider, InboundMessage, OutboundMessage, ProviderSendResult

logger = logging.getLogger("waha_provider")


class WAHAWhatsAppProvider(WhatsAppProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        session: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or getattr(settings, "WAHA_BASE_URL", "http://127.0.0.1:3000")).rstrip("/")
        self.session = session or getattr(settings, "WAHA_SESSION", "default")
        self.api_key = api_key or getattr(settings, "WAHA_API_KEY", "")

    def verify_webhook_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
        # WAHA running locally does not require signature unless X-Api-Key is configured
        return True

    def parse_inbound_webhook(self, payload: Dict[str, Any]) -> List[InboundMessage]:
        messages: List[InboundMessage] = []

        # WAHA sends event: "message"
        event = payload.get("event")
        data = payload.get("payload", {})

        # Do not reply to messages sent by ourselves!
        if data.get("fromMe") is True:
            return []

        sender = data.get("from", "")
        # Clean @c.us suffix
        clean_sender = sender.replace("@c.us", "").replace("@s.whatsapp.net", "").strip()

        # Extract text body
        text = data.get("body", "")
        msg_id = data.get("id", "waha-msg")

        if clean_sender and text:
            messages.append(
                InboundMessage(
                    message_id=str(msg_id),
                    sender_id=str(clean_sender),
                    text=str(text),
                    raw_payload=payload,
                )
            )

        return messages

    def send_message(self, message: OutboundMessage) -> ProviderSendResult:
        # Format chatId for WAHA (e.g. 923001234567@c.us)
        clean_recipient = message.recipient_id.replace("whatsapp:", "").replace("+", "").strip()
        chat_id = clean_recipient if "@" in clean_recipient else f"{clean_recipient}@c.us"

        url = f"{self.base_url}/api/sendText"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        payload = {
            "chatId": chat_id,
            "text": message.text,
            "session": self.session,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code in [200, 201]:
                    data = res.json()
                    msg_id = data.get("id") or "waha-sent"
                    return ProviderSendResult(success=True, provider_message_id=msg_id)
                else:
                    return ProviderSendResult(
                        success=False,
                        error_message=f"WAHA send error {res.status_code}: {res.text[:200]}",
                        should_retry=res.status_code in [429, 500, 502, 503, 504],
                    )
        except Exception as e:
            return ProviderSendResult(
                success=False,
                error_message=f"Network error connecting to WAHA: {str(e)}",
                should_retry=True,
            )
