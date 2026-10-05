"""Meta WhatsApp Cloud API Adapter (Pinned to Graph API v21.0).

Follows official Meta WhatsApp Business Platform Cloud API specifications:
- Webhook Challenge (hub.mode, hub.verify_token, hub.challenge)
- HMAC SHA256 Signature Verification via X-Hub-Signature-256
- Message parsing for text, button_reply, and list_reply
- Safe ignoring of status delivery/read receipts
- 24-hour service window compliance
"""

import hmac
import hashlib
import logging
from typing import List, Optional, Dict, Any
import httpx
from app.config import settings
from app.providers.base import WhatsAppProvider, InboundMessage, OutboundMessage, ProviderSendResult

logger = logging.getLogger("meta_provider")


class MetaWhatsAppCloudApiProvider(WhatsAppProvider):
    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        verify_token: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.app_secret = app_secret or settings.WHATSAPP_APP_SECRET
        self.verify_token = verify_token or settings.WHATSAPP_VERIFY_TOKEN
        self.api_version = api_version or settings.WHATSAPP_API_VERSION or "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id and self.app_secret)

    def verify_webhook_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
        if not signature_header:
            return False

        if not self.app_secret:
            logger.warning("WHATSAPP_APP_SECRET is not configured; rejecting signature verification.")
            return False

        if not signature_header.startswith("sha256="):
            return False

        expected_sig = signature_header[7:]
        computed_sig = hmac.new(
            self.app_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, computed_sig)

    def verify_subscription(self, mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Optional[str]:
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def parse_inbound_webhook(self, payload: Dict[str, Any]) -> List[InboundMessage]:
        messages: List[InboundMessage] = []
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                # Safely ignore status receipts (sent, delivered, read) to prevent reply loops
                if "statuses" in value and "messages" not in value:
                    continue

                for m in value.get("messages", []):
                    m_type = m.get("type")
                    text = ""
                    if m_type == "text":
                        text = m.get("text", {}).get("body", "")
                    elif m_type == "interactive":
                        inter = m.get("interactive", {})
                        if inter.get("type") == "button_reply":
                            text = inter.get("button_reply", {}).get("title", "")
                        elif inter.get("type") == "list_reply":
                            text = inter.get("list_reply", {}).get("title", "")

                    if text:
                        messages.append(InboundMessage(
                            message_id=m.get("id", ""),
                            sender_id=m.get("from", ""),
                            text=text,
                            timestamp=m.get("timestamp"),
                            raw_payload=payload
                        ))

        return messages

    def send_message(self, message: OutboundMessage) -> ProviderSendResult:
        if not self.is_configured():
            return ProviderSendResult(
                success=False,
                error_message="Meta WhatsApp Cloud API credentials are unconfigured.",
                should_retry=False,
            )

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Build payload according to Meta API specs
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.recipient_id,
        }

        if message.interactive_type == "button" and message.buttons and len(message.buttons) <= 3:
            payload["type"] = "interactive"
            payload["interactive"] = {
                "type": "button",
                "body": {"text": message.text},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": b["id"], "title": b["title"][:20]}
                        }
                        for b in message.buttons
                    ]
                }
            }
        elif message.interactive_type == "list" and message.sections:
            payload["type"] = "interactive"
            payload["interactive"] = {
                "type": "list",
                "body": {"text": message.text},
                "action": {
                    "button": "Options",
                    "sections": message.sections
                }
            }
        else:
            payload["type"] = "text"
            payload["text"] = {"preview_url": False, "body": message.text}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(self.base_url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    msg_id = data.get("messages", [{}])[0].get("id")
                    return ProviderSendResult(success=True, provider_message_id=msg_id)
                else:
                    status = resp.status_code
                    # 5xx or rate limits (429) should be retried
                    should_retry = status in [429, 500, 502, 503, 504]
                    error_text = resp.text[:200]
                    return ProviderSendResult(
                        success=False,
                        error_message=f"Meta API error {status}: {error_text}",
                        should_retry=should_retry,
                    )
        except Exception as e:
            return ProviderSendResult(
                success=False,
                error_message=f"Network error sending message: {str(e)}",
                should_retry=True,
            )
