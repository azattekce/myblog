"""JWT doğrulama (tüm servisler). Token'ı yalnızca identity-service üretir."""

import logging
from dataclasses import dataclass

import jwt

from ..config import ServiceSettings
from ..domain import ForbiddenError, UnauthorizedError

REVOKED_JTI_KEY = "auth:revoked:{jti}"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Principal:
    user_id: str
    username: str
    display_name: str
    role: str
    jti: str
    exp: int

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class JwtVerifier:
    def __init__(self, settings: ServiceSettings, redis_client=None) -> None:
        self._s = settings
        self._redis = redis_client

    def verify(self, token: str) -> Principal:
        try:
            claims = jwt.decode(
                token,
                self._s.jwt_secret,
                algorithms=[self._s.jwt_algorithm],
                audience=self._s.jwt_audience,
                issuer=self._s.jwt_issuer,
                options={"require": ["exp", "iat", "sub", "jti", "iss", "aud"]},
                leeway=10,
            )
        except jwt.ExpiredSignatureError as exc:
            raise UnauthorizedError("Erişim token'ının süresi doldu", code="token_expired") from exc
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Geçersiz erişim token'ı", code="invalid_token") from exc

        if claims.get("typ") != "access":
            raise UnauthorizedError("Geçersiz token tipi", code="invalid_token")

        if self._redis is not None:
            try:
                if self._redis.exists(REVOKED_JTI_KEY.format(jti=claims["jti"])):
                    raise UnauthorizedError("Token iptal edilmiş", code="token_revoked")
            except UnauthorizedError:
                raise
            except Exception:  # noqa: BLE001, S110 - redis yoksa fail-open (access token ömrü 15 dk)
                log.warning("Token iptal listesi kontrol edilemedi (fail-open)")

        return Principal(
            user_id=claims["sub"],
            username=claims.get("username", ""),
            display_name=claims.get("name", ""),
            role=claims.get("role", "reader"),
            jti=claims["jti"],
            exp=int(claims["exp"]),
        )


def ensure_admin(principal: Principal) -> Principal:
    if not principal.is_admin:
        raise ForbiddenError("Bu işlem için yönetici yetkisi gerekir")
    return principal
