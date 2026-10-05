"""Provider-neutral WhatsApp adapter interfaces and data classes."""

import hmac
import hashlib
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class InboundMessage(BaseModel):
    message_id: str
    sender_id: str
    text: str
    timestamp: Optional[str] = None
    raw_payload: Dict[str, Any] = {}


class OutboundMessage(BaseModel):
    recipient_id: str
    text: str
    interactive_type: Optional[str] = None  # "button" or "list" or None
    buttons: Optional[List[Dict[str, str]]] = None  # [{"id": "...", "title": "..."}]
    sections: Optional[List[Dict[str, Any]]] = None  # For list messages


class ProviderSendResult(BaseModel):
    success: bool
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    should_retry: bool = False


class WhatsAppProvider(ABC):
    @abstractmethod
    def verify_webhook_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
        """Verify HMAC SHA256 signature from provider."""
        pass

    @abstractmethod
    def parse_inbound_webhook(self, payload: Dict[str, Any]) -> List[InboundMessage]:
        """Extract inbound user messages from webhook payload, ignoring status updates safely."""
        pass

    @abstractmethod
    def send_message(self, message: OutboundMessage) -> ProviderSendResult:
        """Send message via the provider."""
        pass
