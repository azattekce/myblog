from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, Request, Response, status

from app.api.dependencies import client_ip, get_container, get_optional_principal, get_principal
from app.api.schemas import ChangePasswordRequest, LoginRequest, TokenResponse, UserResponse
from app.application.commands import ChangePasswordCommand, LoginCommand, LogoutCommand, RefreshCommand
from app.application.dtos import AuthResult
from app.container import Container
from devblog_common.domain import ForbiddenError, UnauthorizedError
from devblog_common.web import Principal

router = APIRouter(prefix="/api/identity/auth", tags=["auth"])


def _csrf_guard(x_csrf: str | None) -> None:
    # Cookie tabanlı uç noktalar için ek CSRF katmanı: özel header CORS preflight'ı zorunlu kılar.
    if x_csrf != "1":
        raise ForbiddenError("CSRF koruma başlığı eksik", code="csrf_header_missing")


def _set_refresh_cookie(response: Response, container: Container, result: AuthResult) -> None:
    s = container.settings
    response.set_cookie(
        key=s.refresh_cookie_name,
        value=result.refresh_token,
        max_age=s.refresh_token_ttl_days * 24 * 3600,
        path=s.refresh_cookie_path,
        httponly=True,
        secure=s.cookie_secure,
        samesite=s.cookie_samesite,
    )


def _token_response(result: AuthResult) -> TokenResponse:
    return TokenResponse(
        access_token=result.access_token, expires_in=result.expires_in, user=UserResponse(**asdict(result.user))
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, response: Response, c: Container = Depends(get_container)):
    result = c.auth.login(
        LoginCommand(body.username, body.password, client_ip(request), request.headers.get("user-agent"))
    )
    _set_refresh_cookie(response, c, result)
    response.headers["Cache-Control"] = "no-store"
    return _token_response(result)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    c: Container = Depends(get_container),
    x_csrf_protection: str | None = Header(default=None),
):
    _csrf_guard(x_csrf_protection)
    raw = request.cookies.get(c.settings.refresh_cookie_name)
    if not raw:
        raise UnauthorizedError("Oturum bulunamadı", code="missing_refresh_token")
    try:
        result = c.auth.refresh(RefreshCommand(raw, client_ip(request), request.headers.get("user-agent")))
    except UnauthorizedError:
        response.delete_cookie(c.settings.refresh_cookie_name, path=c.settings.refresh_cookie_path)
        raise
    _set_refresh_cookie(response, c, result)
    response.headers["Cache-Control"] = "no-store"
    return _token_response(result)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    c: Container = Depends(get_container),
    principal: Principal | None = Depends(get_optional_principal),
    x_csrf_protection: str | None = Header(default=None),
):
    _csrf_guard(x_csrf_protection)
    c.auth.logout(
        LogoutCommand(
            refresh_token=request.cookies.get(c.settings.refresh_cookie_name),
            access_jti=principal.jti if principal else None,
            access_exp=principal.exp if principal else None,
        )
    )
    response.delete_cookie(c.settings.refresh_cookie_name, path=c.settings.refresh_cookie_path)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest,
    c: Container = Depends(get_container),
    principal: Principal = Depends(get_principal),
):
    c.auth.change_password(ChangePasswordCommand(principal.user_id, body.current_password, body.new_password))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
