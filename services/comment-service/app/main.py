import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import comments
from app.container import build_container, check_database, check_redis
from app.core.config import Settings, get_settings
from devblog_common.web import create_service_app

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, redis_client=None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        c = build_container(settings, redis_client)
        app.state.container = c
        app.state.readiness_checks = {
            "database": lambda a: check_database(a.state.container),
            "redis": lambda a: check_redis(a.state.container),
        }
        if settings.messaging_enabled:
            c.relay.start()
            c.consumer.start()
        log.info("comment-service hazır")
        yield
        if settings.messaging_enabled:
            c.consumer.stop()
            c.relay.stop()
        c.engine.dispose()

    app = create_service_app(settings, title="DevBlog Comment Service", api_prefix="/api/comments", lifespan=lifespan)
    app.include_router(comments.admin)
    app.include_router(comments.public)
    return app


app = create_app()
