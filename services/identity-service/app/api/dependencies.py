from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import Container
from devblog_common.domain import UnauthorizedError
from devblog_common.web import Principal

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    container: Container = Depends(get_container),
) -> Principal:
    if creds is None or creds.scheme.lower() != "bearer":
        raise UnauthorizedError("Kimlik doğrulaması gerekli", code="missing_token")
    return container.verifier.verify(creds.credentials)


def get_optional_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    container: Container = Depends(get_container),
) -> Principal | None:
    if creds is None:
        return None
    try:
        return container.verifier.verify(creds.credentials)
    except UnauthorizedError:
        return None


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None
