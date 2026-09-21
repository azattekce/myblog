import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("MESSAGING_ENABLED", "false")
os.environ.setdefault("ADMIN_PASSWORD", "Admin123!")

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite://", messaging_enabled=False, admin_password="Admin123!")


@pytest.fixture
def client(settings):
    app = create_app(settings, redis_client=fakeredis.FakeRedis(decode_responses=True))
    with TestClient(app) as c:
        yield c
