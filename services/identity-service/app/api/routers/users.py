from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container, get_principal
from app.api.schemas import UserResponse
from app.container import Container
from devblog_common.web import Principal

router = APIRouter(prefix="/api/identity/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def me(principal: Principal = Depends(get_principal), c: Container = Depends(get_container)):
    return UserResponse(**asdict(c.users.get_user(principal.user_id)))
