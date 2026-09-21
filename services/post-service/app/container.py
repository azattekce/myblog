from dataclasses import dataclass

from sqlalchemy import text

from app.application.commands.handlers import PostCommandHandler
from app.application.integration_handlers import CommentEventsHandler
from app.application.queries.handlers import PostQueryHandler
from app.core.config import Settings
from app.infrastructure.persistence.models import Base, OutboxMessage
from app.infrastructure.persistence.read_model import SqlAlchemyPostReadModel
from app.infrastructure.persistence.unit_of_work import SqlAlchemyPostUnitOfWork
from app.infrastructure.view_counter import RedisViewCounter
from devblog_common.cache import RedisCache, create_redis
from devblog_common.messaging import NullPublisher, RabbitMqConsumer, RabbitMqPublisher
from devblog_common.persistence import OutboxRelay, build_engine, build_session_factory, ensure_database
from devblog_common.web import JwtVerifier

COMMENT_EVENTS_QUEUE = "post-service.comment-events"


@dataclass
class Container:
    settings: Settings
    engine: object
    redis: object
    commands: PostCommandHandler
    queries: PostQueryHandler
    verifier: JwtVerifier
    relay: OutboxRelay
    consumer: RabbitMqConsumer | None


def build_container(settings: Settings, redis_client=None) -> Container:
    ensure_database(settings)
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    sf = build_session_factory(engine)
    redis_client = redis_client or create_redis(settings.redis_url)
    cache = RedisCache(redis_client, prefix="cache:post-service")

    commands = PostCommandHandler(lambda: SqlAlchemyPostUnitOfWork(sf), cache)
    queries = PostQueryHandler(
        SqlAlchemyPostReadModel(sf), cache, settings.cache_ttl_seconds, RedisViewCounter(redis_client)
    )
    publisher = (
        RabbitMqPublisher(settings.rabbitmq_url, settings.service_name)
        if settings.messaging_enabled
        else NullPublisher()
    )
    consumer = (
        RabbitMqConsumer(settings.rabbitmq_url, COMMENT_EVENTS_QUEUE, CommentEventsHandler(commands), redis_client)
        if settings.messaging_enabled
        else None
    )
    return Container(
        settings=settings,
        engine=engine,
        redis=redis_client,
        commands=commands,
        queries=queries,
        verifier=JwtVerifier(settings, redis_client),
        relay=OutboxRelay(sf, OutboxMessage, publisher, settings.outbox_poll_interval),
        consumer=consumer,
    )


def check_database(c: Container) -> None:
    with c.engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def check_redis(c: Container) -> None:
    c.redis.ping()
