from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import Container
from devblog_common.domain import UnauthorizedError
from devblog_common.web import Principal
from devblog_common.web.security import ensure_admin

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    container: Container = Depends(get_container),
) -> Principal:
    if creds is None:
        raise UnauthorizedError("Kimlik doğrulaması gerekli", code="missing_token")
    return container.verifier.verify(creds.credentials)


def require_admin(principal: Principal = Depends(get_principal)) -> Principal:
    return ensure_admin(principal)
