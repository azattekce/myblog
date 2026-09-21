from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from devblog_common.clock import utcnow
from devblog_common.domain import new_id


@dataclass
class RefreshToken:
    """Rotasyonlu refresh token. Aynı 'family' içindeki iptal edilmiş bir token'ın
    tekrar kullanılması çalıntı token göstergesidir ve tüm aile iptal edilir."""

    id: str
    user_id: str
    token_hash: str
    family_id: str
    expires_at: datetime
    created_at: datetime = field(default_factory=utcnow)
    revoked_at: datetime | None = None
    replaced_by_id: str | None = None
    created_by_ip: str | None = None
    user_agent: str | None = None

    @classmethod
    def issue(
        cls,
        user_id: str,
        token_hash: str,
        ttl: timedelta,
        family_id: str | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshToken:
        return cls(
            id=new_id(),
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id or new_id(),
            expires_at=utcnow() + ttl,
            created_by_ip=ip,
            user_agent=(user_agent or "")[:256] or None,
        )

    @property
    def is_expired(self) -> bool:
        return utcnow() >= self.expires_at

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_active(self) -> bool:
        return not self.is_expired and not self.is_revoked

    def revoke(self, replaced_by_id: str | None = None) -> None:
        if self.revoked_at is None:
            self.revoked_at = utcnow()
            self.replaced_by_id = replaced_by_id
