from datetime import timedelta

import pytest

from app.domain.refresh_token import RefreshToken
from app.domain.user import Role, User
from devblog_common.domain import BusinessRuleViolation, ForbiddenError


def test_register_normalizes_and_emits_event():
    user = User.register("Mehmet", "M@Example.com", "Mehmet", "hash", Role.ADMIN)
    assert user.username == "mehmet"
    assert user.email == "m@example.com"
    events = user.pull_events()
    assert [e.name for e in events] == ["user.registered"]
    assert user.pull_events() == []


@pytest.mark.parametrize("username", ["ab", "bad name", "x" * 51])
def test_register_rejects_invalid_username(username):
    with pytest.raises(BusinessRuleViolation):
        User.register(username, "a@b.co", "x", "hash", Role.READER)


def test_inactive_user_cannot_login():
    user = User.register("reader1", "r@b.co", "R", "hash", Role.READER)
    user.is_active = False
    with pytest.raises(ForbiddenError):
        user.ensure_can_login()


def test_refresh_token_lifecycle():
    token = RefreshToken.issue("u1", "h", timedelta(days=1))
    assert token.is_active
    token.revoke(replaced_by_id="t2")
    assert token.is_revoked and token.replaced_by_id == "t2"
    expired = RefreshToken.issue("u1", "h2", timedelta(seconds=-1))
    assert expired.is_expired
