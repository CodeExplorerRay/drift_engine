from __future__ import annotations

from dataclasses import dataclass

from config.logging_config import get_logger
from drift_engine.events.models import Event

logger = get_logger(__name__)


@dataclass(slots=True)
class WebhookNotifier:
    url: str
    timeout_seconds: float = 5.0

    async def send(self, event: Event) -> None:
        try:
            import httpx
        except ImportError:
            logger.warning("webhook_notifier_unavailable", reason="httpx is not installed")
            return

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self.url, json=event.to_document())
            response.raise_for_status()
