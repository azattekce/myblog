from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC datetime (MSSQL DATETIME2 ile uyumlu, timezone bilgisi taşımaz)."""
    return datetime.now(UTC).replace(tzinfo=None)


def to_iso_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value.isoformat(timespec="seconds") + "Z"
