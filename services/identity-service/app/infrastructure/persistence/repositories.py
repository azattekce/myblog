"""Repository Pattern: ORM modelleri <-> domain nesneleri eşlemesi. Domain, ORM'i bilmez."""

from collections.abc import Callable

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.domain.refresh_token import RefreshToken
from app.domain.repositories import RefreshTokenRepository, UserRepository
from app.domain.user import Role, User
from devblog_common.clock import utcnow

from .models import RefreshTokenModel, UserModel


def _to_user(m: UserModel) -> User:
    return User(
        id=m.id,
        username=m.username,
        email=m.email,
        display_name=m.display_name,
        password_hash=m.password_hash,
        role=Role(m.role),
        is_active=m.is_active,
        created_at=m.created_at,
        last_login_at=m.last_login_at,
    )


def _to_token(m: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=m.id,
        user_id=m.user_id,
        token_hash=m.token_hash,
        family_id=m.family_id,
        expires_at=m.expires_at,
        created_at=m.created_at,
        revoked_at=m.revoked_at,
        replaced_by_id=m.replaced_by_id,
        created_by_ip=m.created_by_ip,
        user_agent=m.user_agent,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session, track: Callable) -> None:
        self._s = session
        self._track = track

    def get_by_id(self, user_id: str) -> User | None:
        m = self._s.get(UserModel, user_id)
        return self._tracked(_to_user(m)) if m else None

    def get_by_username(self, username: str) -> User | None:
        m = self._s.execute(select(UserModel).where(UserModel.username == username)).scalar_one_or_none()
        return self._tracked(_to_user(m)) if m else None

    def exists(self, username: str, email: str) -> bool:
        q = select(UserModel.id).where(or_(UserModel.username == username, UserModel.email == email))
        return self._s.execute(q).first() is not None

    def add(self, user: User) -> None:
        self._s.add(
            UserModel(
                id=user.id,
                username=user.username,
                email=user.email,
                display_name=user.display_name,
                password_hash=user.password_hash,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
            )
        )
        self._track(user)

    def update(self, user: User) -> None:
        m = self._s.get(UserModel, user.id)
        m.email, m.display_name, m.password_hash = user.email, user.display_name, user.password_hash
        m.role, m.is_active, m.last_login_at = user.role.value, user.is_active, user.last_login_at
        self._track(user)

    def _tracked(self, user: User) -> User:
        self._track(user)
        return user


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        m = self._s.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        ).scalar_one_or_none()
        return _to_token(m) if m else None

    def add(self, token: RefreshToken) -> None:
        self._s.add(
            RefreshTokenModel(
                id=token.id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                family_id=token.family_id,
                expires_at=token.expires_at,
                created_at=token.created_at,
                revoked_at=token.revoked_at,
                replaced_by_id=token.replaced_by_id,
                created_by_ip=token.created_by_ip,
                user_agent=token.user_agent,
            )
        )

    def update(self, token: RefreshToken) -> None:
        m = self._s.get(RefreshTokenModel, token.id)
        m.revoked_at, m.replaced_by_id = token.revoked_at, token.replaced_by_id

    def revoke_family(self, family_id: str) -> int:
        result = self._s.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.family_id == family_id, RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        return result.rowcount or 0
