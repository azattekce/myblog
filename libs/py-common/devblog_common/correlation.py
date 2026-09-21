import re
import uuid
from contextvars import ContextVar

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")
_SAFE = re.compile(r"^[A-Za-z0-9._\-]{1,64}$")


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(value: str | None):
    if not value or not _SAFE.match(value):
        value = str(uuid.uuid4())
    return _correlation_id.set(value)


def reset_correlation_id(token) -> None:
    _correlation_id.reset(token)
