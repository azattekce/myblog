import logging
import time

from ..correlation import get_correlation_id, reset_correlation_id, set_correlation_id

log = logging.getLogger("http")
_SKIP = ("/health", "/metrics")


class RequestContextMiddleware:
    """Pure ASGI middleware: correlation-id yayılımı + yapılandırılmış erişim logu."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        incoming = headers.get(b"x-request-id") or headers.get(b"x-correlation-id") or b""
        token = set_correlation_id(incoming.decode("latin-1"))
        cid = get_correlation_id()
        started = time.perf_counter()
        status_holder = {"status": 500}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                message["headers"] = [*message.get("headers", []), (b"x-request-id", cid.encode())]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            path = scope.get("path", "")
            if not path.startswith(_SKIP):
                log.info(
                    "request",
                    extra={
                        "method": scope.get("method"),
                        "path": path,
                        "status": status_holder["status"],
                        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                        "client_ip": (scope.get("client") or ("-",))[0],
                    },
                )
            reset_correlation_id(token)
