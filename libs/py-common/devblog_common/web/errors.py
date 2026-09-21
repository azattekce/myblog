"""Domain hatalarını RFC 7807 (application/problem+json) cevaplarına dönüştürür."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..correlation import get_correlation_id
from ..domain import (
    BusinessRuleViolation,
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
    UnauthorizedError,
)

log = logging.getLogger(__name__)

_STATUS = {
    NotFoundError: 404,
    ConflictError: 409,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    RateLimitedError: 429,
    BusinessRuleViolation: 422,
}


def problem(status: int, code: str, detail: str, errors: list | None = None) -> JSONResponse:
    body = {
        "type": f"https://devblog.local/problems/{code}",
        "title": code.replace("_", " ").capitalize(),
        "status": status,
        "detail": detail,
        "code": code,
        "correlation_id": get_correlation_id(),
    }
    if errors:
        body["errors"] = errors
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(status_code=status, content=body, media_type="application/problem+json", headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError):
        status = next((s for cls, s in _STATUS.items() if isinstance(exc, cls)), 400)
        if status >= 500:
            log.error("Domain hatası", extra={"code": exc.code})
        return problem(status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(p) for p in e.get("loc", [])[1:]), "message": e.get("msg")} for e in exc.errors()
        ]
        return problem(422, "validation_error", "İstek doğrulanamadı", errors)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        return problem(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        log.exception("Beklenmeyen hata")
        return problem(500, "internal_error", "Beklenmeyen bir hata oluştu")
