"""Tüm servislerde aynı cross-cutting concern'leri kuran FastAPI fabrikası."""

from collections.abc import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from ..config import ServiceSettings
from ..logging import configure_logging
from .errors import register_exception_handlers
from .middleware import RequestContextMiddleware

ReadinessCheck = Callable[[FastAPI], None]


def create_service_app(
    settings: ServiceSettings,
    *,
    title: str,
    api_prefix: str,
    version: str = "1.0.0",
    lifespan=None,
) -> FastAPI:
    configure_logging(settings.service_name, settings.log_level, settings.environment)
    docs = not settings.is_production
    app = FastAPI(
        title=title,
        version=version,
        lifespan=lifespan,
        docs_url=f"{api_prefix}/docs" if docs else None,
        redoc_url=None,
        openapi_url=f"{api_prefix}/openapi.json" if docs else None,
    )
    app.state.readiness_checks = {}
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    Instrumentator(
        excluded_handlers=["/metrics", "/health/live", "/health/ready"],
        should_group_status_codes=True,
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    @app.get("/health/live", include_in_schema=False)
    def live():
        return {"status": "alive", "service": settings.service_name}

    @app.get("/health/ready", include_in_schema=False)
    def ready():
        results, ok = {}, True
        for name, check in app.state.readiness_checks.items():
            try:
                check(app)
                results[name] = "up"
            except Exception as exc:  # noqa: BLE001
                ok = False
                results[name] = f"down: {str(exc)[:120]}"
        return JSONResponse(
            status_code=200 if ok else 503, content={"status": "ready" if ok else "degraded", "checks": results}
        )

    return app
