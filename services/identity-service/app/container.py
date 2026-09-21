"""Composition Root: tüm bağımlılıklar tek bir yerde bağlanır."""

from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import text

from app.application.handlers import AuthCommandHandler, UserQueryHandler
from app.core.config import Settings
from app.infrastructure.cache.redis_stores import RedisLoginThrottle, RedisTokenRevocationStore
from app.infrastructure.persistence.models import Base, OutboxMessage
from app.infrastructure.persistence.unit_of_work import SqlAlchemyIdentityUnitOfWork
from app.infrastructure.security.password import Argon2PasswordHasher
from app.infrastructure.security.tokens import JwtAccessTokenIssuer, OpaqueRefreshTokenGenerator
from devblog_common.cache import create_redis
from devblog_common.messaging import NullPublisher, RabbitMqPublisher
from devblog_common.persistence import OutboxRelay, build_engine, build_session_factory, ensure_database
from devblog_common.web import JwtVerifier


@dataclass
class Container:
    settings: Settings
    engine: object
    redis: object
    auth: AuthCommandHandler
    users: UserQueryHandler
    verifier: JwtVerifier
    relay: OutboxRelay | None = None
    background: list = field(default_factory=list)


def build_container(settings: Settings, redis_client=None) -> Container:
    ensure_database(settings)
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    redis_client = redis_client or create_redis(settings.redis_url)

    def uow_factory():
        return SqlAlchemyIdentityUnitOfWork(session_factory)

    auth = AuthCommandHandler(
        uow_factory=uow_factory,
        hasher=Argon2PasswordHasher(),
        access_issuer=JwtAccessTokenIssuer(settings),
        refresh_generator=OpaqueRefreshTokenGenerator(),
        revocation_store=RedisTokenRevocationStore(redis_client),
        throttle=RedisLoginThrottle(redis_client, settings.login_max_attempts, settings.login_lock_minutes),
        refresh_ttl=timedelta(days=settings.refresh_token_ttl_days),
    )
    publisher = (
        RabbitMqPublisher(settings.rabbitmq_url, settings.service_name)
        if settings.messaging_enabled
        else NullPublisher()
    )
    relay = OutboxRelay(session_factory, OutboxMessage, publisher, settings.outbox_poll_interval)
    return Container(
        settings=settings,
        engine=engine,
        redis=redis_client,
        auth=auth,
        users=UserQueryHandler(uow_factory),
        verifier=JwtVerifier(settings, redis_client),
        relay=relay,
    )


def check_database(container: Container) -> None:
    with container.engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def check_redis(container: Container) -> None:
    container.redis.ping()
