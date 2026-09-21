from typing import Any

from ..clock import to_iso_z
from ..correlation import get_correlation_id
from ..domain import DomainEvent


def build_envelope(event: DomainEvent, source: str) -> dict[str, Any]:
    """Tüm integration event'ler için standart zarf (CloudEvents'ten esinlenilmiştir)."""
    return {
        "event_id": event.event_id,
        "event_type": event.name,
        "version": event.version,
        "occurred_at": to_iso_z(event.occurred_at),
        "source": source,
        "correlation_id": get_correlation_id(),
        "payload": event.payload,
    }
