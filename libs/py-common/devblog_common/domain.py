"""Shared kernel: domain katmanı için saf Python yapı taşları (framework bağımlılığı yok)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .clock import utcnow


def new_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class DomainEvent:
    """Aggregate içinde oluşan olay. Outbox aracılığıyla integration event'e dönüşür."""

    name: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=new_id)
    occurred_at: datetime = field(default_factory=utcnow)
    version: int = 1


class AggregateRoot:
    """Domain event biriktirebilen aggregate kökü (dataclass'larla uyumlu mixin)."""

    def _pending_events(self) -> list[DomainEvent]:
        if "_domain_events" not in self.__dict__:
            self.__dict__["_domain_events"] = []
        return self.__dict__["_domain_events"]

    def record_event(self, name: str, payload: dict[str, Any]) -> None:
        self._pending_events().append(DomainEvent(name=name, payload=payload))

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._pending_events())
        self._pending_events().clear()
        return events


# ---------------------------------------------------------------- exceptions
class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class BusinessRuleViolation(DomainError):
    code = "business_rule_violation"


class NotFoundError(DomainError):
    code = "not_found"


class ConflictError(DomainError):
    code = "conflict"


class UnauthorizedError(DomainError):
    code = "unauthorized"


class ForbiddenError(DomainError):
    code = "forbidden"


class RateLimitedError(DomainError):
    code = "rate_limited"
