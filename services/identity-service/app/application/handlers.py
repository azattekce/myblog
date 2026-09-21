"""Command & Query handler'ları (CQRS). İş akışını yönetir, altyapıyı portlar üzerinden kullanır."""

import logging
import time
from collections.abc import Callable
from datetime import timedelta

from app.application.commands import (
    ChangePasswordCommand,
    LoginCommand,
    LogoutCommand,
    RefreshCommand,
    SeedAdminCommand,
)
from app.application.dtos import AuthResult, UserDto
from app.application.interfaces import (
    AccessTokenIssuer,
    IdentityUnitOfWork,
    LoginThrottle,
    PasswordHasher,
    RefreshTokenGenerator,
    TokenRevocationStore,
)
from app.domain.refresh_token import RefreshToken
from app.domain.user import Role, User
from devblog_common.domain import BusinessRuleViolation, NotFoundError, RateLimitedError, UnauthorizedError

log = logging.getLogger(__name__)
_INVALID = "Kullanıcı adı veya parola hatalı"


class AuthCommandHandler:
    def __init__(
        self,
        uow_factory: Callable[[], IdentityUnitOfWork],
        hasher: PasswordHasher,
        access_issuer: AccessTokenIssuer,
        refresh_generator: RefreshTokenGenerator,
        revocation_store: TokenRevocationStore,
        throttle: LoginThrottle,
        refresh_ttl: timedelta,
    ) -> None:
        self._uow = uow_factory
        self._hasher = hasher
        self._access = access_issuer
        self._refresh = refresh_generator
        self._revocation = revocation_store
        self._throttle = throttle
        self._refresh_ttl = refresh_ttl

    # ------------------------------------------------------------- login
    def login(self, cmd: LoginCommand) -> AuthResult:
        throttle_key = f"{cmd.username.lower()}:{cmd.ip or '-'}"
        if self._throttle.is_locked(throttle_key):
            raise RateLimitedError("Çok fazla başarısız deneme. Lütfen daha sonra tekrar deneyin.")

        with self._uow() as uow:
            user = uow.users.get_by_username(cmd.username.lower())
            if user is None or not self._hasher.verify(user.password_hash, cmd.password):
                self._throttle.register_failure(throttle_key)
                log.warning("Başarısız giriş denemesi", extra={"username": cmd.username, "ip": cmd.ip})
                raise UnauthorizedError(_INVALID, code="invalid_credentials")

            user.ensure_can_login()
            if self._hasher.needs_rehash(user.password_hash):
                user.change_password_hash(self._hasher.hash(cmd.password))
            user.record_login(cmd.ip)
            uow.users.update(user)

            raw, token = self._new_refresh_token(user, None, cmd.ip, cmd.user_agent)
            uow.refresh_tokens.add(token)
            uow.commit()

        self._throttle.reset(throttle_key)
        access, expires_in = self._access.issue(user)
        log.info("Kullanıcı giriş yaptı", extra={"user_id": user.id})
        return AuthResult(access, expires_in, raw, token.expires_at, UserDto.from_domain(user))

    # ----------------------------------------------------------- refresh
    def refresh(self, cmd: RefreshCommand) -> AuthResult:
        token_hash = self._refresh.hash(cmd.refresh_token)
        with self._uow() as uow:
            current = uow.refresh_tokens.get_by_hash(token_hash)
            if current is None:
                raise UnauthorizedError("Oturum bulunamadı", code="invalid_refresh_token")

            if current.is_revoked:
                revoked = uow.refresh_tokens.revoke_family(current.family_id)
                uow.commit()
                log.warning(
                    "Refresh token yeniden kullanımı tespit edildi, token ailesi iptal edildi",
                    extra={"user_id": current.user_id, "family_id": current.family_id, "revoked": revoked},
                )
                raise UnauthorizedError("Oturum geçersiz kılındı", code="refresh_token_reused")

            if current.is_expired:
                raise UnauthorizedError("Oturum süresi doldu", code="refresh_token_expired")

            user = uow.users.get_by_id(current.user_id)
            if user is None:
                raise UnauthorizedError("Kullanıcı bulunamadı", code="invalid_refresh_token")
            user.ensure_can_login()

            raw, new_token = self._new_refresh_token(user, current.family_id, cmd.ip, cmd.user_agent)
            current.revoke(replaced_by_id=new_token.id)
            uow.refresh_tokens.update(current)
            uow.refresh_tokens.add(new_token)
            uow.commit()

        access, expires_in = self._access.issue(user)
        return AuthResult(access, expires_in, raw, new_token.expires_at, UserDto.from_domain(user))

    # ------------------------------------------------------------ logout
    def logout(self, cmd: LogoutCommand) -> None:
        if cmd.refresh_token:
            with self._uow() as uow:
                token = uow.refresh_tokens.get_by_hash(self._refresh.hash(cmd.refresh_token))
                if token is not None:
                    uow.refresh_tokens.revoke_family(token.family_id)
                    uow.commit()
        if cmd.access_jti and cmd.access_exp:
            ttl = max(int(cmd.access_exp - time.time()), 1)
            self._revocation.revoke_access_token(cmd.access_jti, ttl)

    # --------------------------------------------------- change password
    def change_password(self, cmd: ChangePasswordCommand) -> None:
        if len(cmd.new_password) < 10:
            raise BusinessRuleViolation("Yeni parola en az 10 karakter olmalı")
        with self._uow() as uow:
            user = uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise NotFoundError("Kullanıcı bulunamadı")
            if not self._hasher.verify(user.password_hash, cmd.current_password):
                raise UnauthorizedError("Mevcut parola hatalı", code="invalid_credentials")
            user.change_password_hash(self._hasher.hash(cmd.new_password))
            uow.users.update(user)
            uow.commit()

    # -------------------------------------------------------- seed admin
    def seed_admin(self, cmd: SeedAdminCommand) -> bool:
        with self._uow() as uow:
            if uow.users.exists(cmd.username.lower(), cmd.email.lower()):
                return False
            admin = User.register(
                cmd.username, cmd.email, cmd.display_name, self._hasher.hash(cmd.password), Role.ADMIN
            )
            uow.users.add(admin)
            uow.commit()
            log.info("Yönetici hesabı oluşturuldu", extra={"username": admin.username})
            return True

    # ---------------------------------------------------------- helpers
    def _new_refresh_token(self, user: User, family_id: str | None, ip: str | None, ua: str | None):
        raw = self._refresh.generate()
        token = RefreshToken.issue(user.id, self._refresh.hash(raw), self._refresh_ttl, family_id, ip, ua)
        return raw, token


class UserQueryHandler:
    def __init__(self, uow_factory: Callable[[], IdentityUnitOfWork]) -> None:
        self._uow = uow_factory

    def get_user(self, user_id: str) -> UserDto:
        with self._uow() as uow:
            user = uow.users.get_by_id(user_id)
            if user is None:
                raise NotFoundError("Kullanıcı bulunamadı")
            return UserDto.from_domain(user)
