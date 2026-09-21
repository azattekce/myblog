import os
import time
import uuid
from datetime import UTC, datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("MESSAGING_ENABLED", "false")

import fakeredis  # noqa: E402
import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite://", messaging_enabled=False)


def make_token(settings: Settings, role: str = "admin") -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": "u-1",
            "username": "admin",
            "name": "Blog Yazarı",
            "role": role,
            "typ": "access",
            "jti": str(uuid.uuid4()),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def client(settings):
    app = create_app(settings, redis_client=fakeredis.FakeRedis(decode_responses=True))
    with TestClient(app) as c:
        c.app_container = app.state.container
        yield c


@pytest.fixture
def admin_headers(settings):
    return {"Authorization": f"Bearer {make_token(settings)}"}


@pytest.fixture
def reader_headers(settings):
    return {"Authorization": f"Bearer {make_token(settings, 'reader')}"}


_ = time
