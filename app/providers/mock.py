"""Mock WhatsApp provider for local simulation, testing, and offline development."""

import logging
from typing import List, Optional, Dict, Any
from app.providers.base import WhatsAppProvider, InboundMessage, OutboundMessage, ProviderSendResult

logger = logging.getLogger("mock_provider")


def mask_phone(phone: str) -> str:
    """Mask phone identifier for privacy in routine logs (e.g. +92300****123)."""
    if len(phone) > 7:
        return f"{phone[:6]}****{phone[-3:]}"
    return "****"


class MockWhatsAppProvider(WhatsAppProvider):
    def __init__(self):
        self.sent_messages: List[OutboundMessage] = []
        self.should_fail_send: bool = False
        self.fail_should_retry: bool = True

    def verify_webhook_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
        # For mock provider, accept if header matches "mock-valid" or if in development
        if signature_header == "invalid_sig":
            return False
        return True

    def parse_inbound_webhook(self, payload: Dict[str, Any]) -> List[InboundMessage]:
        messages: List[InboundMessage] = []
        # Support direct format: {"sender_id": "...", "text": "...", "message_id": "..."}
        if "sender_id" in payload and "text" in payload:
            msg_id = payload.get("message_id", f"mock-msg-{len(messages)+1}")
            messages.append(InboundMessage(
                message_id=msg_id,
                sender_id=payload["sender_id"],
                text=payload["text"],
                raw_payload=payload
            ))
            return messages

        # Support Meta-like format in mock
        entry_list = payload.get("entry", [])
        for entry in entry_list:
            changes = entry.get("changes", [])
            for change in changes:
                val = change.get("value", {})
                # Ignore status events
                if "statuses" in val and "messages" not in val:
                    continue
                meta_msgs = val.get("messages", [])
                for m in meta_msgs:
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
                            message_id=m.get("id", "mock-id"),
                            sender_id=m.get("from", ""),
                            text=text,
                            timestamp=m.get("timestamp"),
                            raw_payload=payload
                        ))

        return messages

    def send_message(self, message: OutboundMessage) -> ProviderSendResult:
        if self.should_fail_send:
            return ProviderSendResult(
                success=False,
                error_message="Mock provider simulated send failure",
                should_retry=self.fail_should_retry,
            )

        self.sent_messages.append(message)
        masked = mask_phone(message.recipient_id)
        logger.info(f"[MockProvider] Sent message to {masked}: {message.text[:50]}...")
        return ProviderSendResult(
            success=True,
            provider_message_id=f"mock-out-{len(self.sent_messages)}",
        )
