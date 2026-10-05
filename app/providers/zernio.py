"""Zernio WhatsApp Provider Adapter (docs.zernio.com).

Supports:
- Zernio Webhook parsing (`message.received` event)
- Direct message sending via `https://api.zernio.com/v1/inbox/messages`
- Signature & secret token verification
"""

import hmac
import hashlib
import logging
from typing import List, Optional, Dict, Any
import httpx
from app.config import settings
from app.providers.base import WhatsAppProvider, InboundMessage, OutboundMessage, ProviderSendResult

logger = logging.getLogger("zernio_provider")


class ZernioWhatsAppProvider(WhatsAppProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.api_key = api_key or getattr(settings, "ZERNIO_API_KEY", "")
        self.phone_number_id = phone_number_id or getattr(settings, "ZERNIO_PHONE_NUMBER_ID", "")
        self.webhook_secret = webhook_secret or getattr(settings, "ZERNIO_WEBHOOK_SECRET", "")
        self.base_url = "https://api.zernio.com/v1/inbox/messages"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def verify_webhook_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
        if not self.webhook_secret:
            # If no secret configured in dev, accept
            return True

        if not signature_header:
            return False

        # Zernio supports HMAC SHA256 or bearer secret token header
        if signature_header.startswith("sha256="):
            expected = signature_header[7:]
            computed = hmac.new(
                self.webhook_secret.encode("utf-8"),
                raw_body,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected, computed)

        return hmac.compare_digest(signature_header, self.webhook_secret)

    def parse_inbound_webhook(self, payload: Dict[str, Any]) -> List[InboundMessage]:
        messages: List[InboundMessage] = []

        # Zernio format: event == "message.received" or direct payload
        event_type = payload.get("event")
        data = payload.get("data", payload.get("message", payload))

        # Check if message payload is present
        if isinstance(data, dict):
            sender = (
                data.get("from")
                or data.get("sender_id")
                or data.get("phone")
                or data.get("author", {}).get("id")
            )
            text = (
                data.get("text")
                or data.get("body")
                or data.get("content", {}).get("text")
            )
            msg_id = data.get("id") or data.get("message_id") or "zernio-msg"

            # Handle interactive button reply or list selection
            if not text and "interactive" in data:
                inter = data["interactive"]
                text = inter.get("button_reply", {}).get("title") or inter.get("list_reply", {}).get("title")

            if sender and text:
                messages.append(
                    InboundMessage(
                        message_id=str(msg_id),
                        sender_id=str(sender),
                        text=str(text),
                        raw_payload=payload,
                    )
                )

        return messages

    def send_message(self, message: OutboundMessage) -> ProviderSendResult:
        if not self.is_configured():
            return ProviderSendResult(
                success=False,
                error_message="ZERNIO_API_KEY is not configured.",
                should_retry=False,
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "recipient": message.recipient_id,
            "type": "text",
            "message": {
                "text": message.text,
            },
        }

        # If phone_number_id is set, specify channel
        if self.phone_number_id:
            payload["channel_id"] = self.phone_number_id

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(self.base_url, headers=headers, json=payload)
                if res.status_code in [200, 201]:
                    data = res.json()
                    msg_id = data.get("id") or data.get("message_id")
                    return ProviderSendResult(success=True, provider_message_id=msg_id)
                else:
                    return ProviderSendResult(
                        success=False,
                        error_message=f"Zernio API error {res.status_code}: {res.text[:200]}",
                        should_retry=res.status_code in [429, 500, 502, 503, 504],
                    )
        except Exception as e:
            return ProviderSendResult(
                success=False,
                error_message=f"Network error sending via Zernio: {str(e)}",
                should_retry=True,
            )
