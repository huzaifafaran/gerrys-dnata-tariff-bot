"""WhatsApp providers package."""

from app.config import settings
from app.providers.base import WhatsAppProvider, InboundMessage, OutboundMessage, ProviderSendResult
from app.providers.mock import MockWhatsAppProvider
from app.providers.meta import MetaWhatsAppCloudApiProvider
from app.providers.zernio import ZernioWhatsAppProvider
from app.providers.waha import WAHAWhatsAppProvider

_mock_instance = MockWhatsAppProvider()


def get_whatsapp_provider() -> WhatsAppProvider:
    if settings.WHATSAPP_PROVIDER == "meta":
        return MetaWhatsAppCloudApiProvider()
    elif settings.WHATSAPP_PROVIDER == "zernio":
        return ZernioWhatsAppProvider()
    elif settings.WHATSAPP_PROVIDER == "waha":
        return WAHAWhatsAppProvider()
    return _mock_instance


__all__ = [
    "WhatsAppProvider",
    "InboundMessage",
    "OutboundMessage",
    "ProviderSendResult",
    "MockWhatsAppProvider",
    "MetaWhatsAppCloudApiProvider",
    "ZernioWhatsAppProvider",
    "WAHAWhatsAppProvider",
    "get_whatsapp_provider",
]
