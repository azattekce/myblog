from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from devblog_common.clock import to_iso_z


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    role: str
    last_login_at: datetime | None = None

    @field_serializer("last_login_at")
    def _ser(self, v):
        return to_iso_z(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse
