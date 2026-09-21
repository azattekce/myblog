import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import auth, users
from app.application.commands import SeedAdminCommand
from app.container import build_container, check_database, check_redis
from app.core.config import Settings, get_settings
from devblog_common.web import create_service_app

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, redis_client=None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        container = build_container(settings, redis_client)
        app.state.container = container
        app.state.readiness_checks = {
            "database": lambda a: check_database(a.state.container),
            "redis": lambda a: check_redis(a.state.container),
        }
        container.auth.seed_admin(
            SeedAdminCommand(
                settings.admin_username, settings.admin_email, settings.admin_display_name, settings.admin_password
            )
        )
        if settings.messaging_enabled:
            container.relay.start()
        log.info("identity-service hazır")
        yield
        if settings.messaging_enabled:
            container.relay.stop()
        container.engine.dispose()

    app = create_service_app(settings, title="DevBlog Identity Service", api_prefix="/api/identity", lifespan=lifespan)
    app.include_router(auth.router)
    app.include_router(users.router)
    return app


app = create_app()
