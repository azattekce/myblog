from dataclasses import dataclass

from sqlalchemy import text

from app.application.handlers import CommentCommandHandler, CommentQueryHandler, PostEventsHandler
from app.core.config import Settings
from app.infrastructure.persistence.models import Base, OutboxMessage
from app.infrastructure.persistence.repositories import SqlAlchemyCommentReadModel
from app.infrastructure.persistence.unit_of_work import SqlAlchemyCommentUnitOfWork
from app.infrastructure.rate_limiter import RedisFixedWindowRateLimiter
from devblog_common.cache import RedisCache, create_redis
from devblog_common.messaging import NullPublisher, RabbitMqConsumer, RabbitMqPublisher
from devblog_common.persistence import OutboxRelay, build_engine, build_session_factory, ensure_database
from devblog_common.web import JwtVerifier

POST_EVENTS_QUEUE = "comment-service.post-events"


@dataclass
class Container:
    settings: Settings
    engine: object
    redis: object
    commands: CommentCommandHandler
    queries: CommentQueryHandler
    post_events: PostEventsHandler
    verifier: JwtVerifier
    relay: OutboxRelay
    consumer: RabbitMqConsumer | None


def build_container(settings: Settings, redis_client=None) -> Container:
    ensure_database(settings)
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    sf = build_session_factory(engine)
    redis_client = redis_client or create_redis(settings.redis_url)
    cache = RedisCache(redis_client, prefix="cache:comment-service")

    def uow_factory():
        return SqlAlchemyCommentUnitOfWork(sf)

    limiter = RedisFixedWindowRateLimiter(
        redis_client, settings.comment_rate_limit, settings.comment_rate_window_seconds
    )
    post_events = PostEventsHandler(uow_factory, cache)
    publisher = (
        RabbitMqPublisher(settings.rabbitmq_url, settings.service_name)
        if settings.messaging_enabled
        else NullPublisher()
    )
    consumer = (
        RabbitMqConsumer(settings.rabbitmq_url, POST_EVENTS_QUEUE, post_events, redis_client)
        if settings.messaging_enabled
        else None
    )
    return Container(
        settings=settings,
        engine=engine,
        redis=redis_client,
        commands=CommentCommandHandler(uow_factory, limiter, cache, settings.ip_hash_salt),
        queries=CommentQueryHandler(SqlAlchemyCommentReadModel(sf), cache, settings.cache_ttl_seconds),
        post_events=post_events,
        verifier=JwtVerifier(settings, redis_client),
        relay=OutboxRelay(sf, OutboxMessage, publisher, settings.outbox_poll_interval),
        consumer=consumer,
    )


def check_database(c: Container) -> None:
    with c.engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def check_redis(c: Container) -> None:
    c.redis.ping()
