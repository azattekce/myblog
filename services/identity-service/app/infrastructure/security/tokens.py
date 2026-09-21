import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import Settings
from app.domain.user import User


class JwtAccessTokenIssuer:
    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def issue(self, user: User) -> tuple[str, int]:
        now = datetime.now(UTC)
        ttl = timedelta(minutes=self._s.access_token_ttl_minutes)
        claims = {
            "sub": user.id,
            "username": user.username,
            "name": user.display_name,
            "role": user.role.value,
            "typ": "access",
            "jti": str(uuid.uuid4()),
            "iss": self._s.jwt_issuer,
            "aud": self._s.jwt_audience,
            "iat": now,
            "nbf": now,
            "exp": now + ttl,
        }
        return jwt.encode(claims, self._s.jwt_secret, algorithm=self._s.jwt_algorithm), int(ttl.total_seconds())


class OpaqueRefreshTokenGenerator:
    """Refresh token'lar opak ve rastgeledir; veritabanında sadece SHA-256 özeti saklanır."""

    def generate(self) -> str:
        return secrets.token_urlsafe(48)

    def hash(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()
