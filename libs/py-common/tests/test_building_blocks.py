"""Paylaşılan çekirdeğin (shared kernel) birim testleri. Tüm servisler bu davranışlara güvenir."""

import time
import uuid

import fakeredis
import jwt
import pytest
import redis

from devblog_common.backoff import Backoff
from devblog_common.cache import RedisCache
from devblog_common.config import ServiceSettings
from devblog_common.correlation import reset_correlation_id, set_correlation_id
from devblog_common.domain import DomainEvent, ForbiddenError, UnauthorizedError
from devblog_common.messaging.envelope import build_envelope
from devblog_common.messaging.topology import QUEUES
from devblog_common.web.security import REVOKED_JTI_KEY, JwtVerifier, ensure_admin

SETTINGS = ServiceSettings(jwt_secret="unit-test-secret-at-least-32-characters!")


def _token(**over):
    now = int(time.time())
    claims = {
        "sub": "u1", "username": "admin", "name": "Yazar", "role": "admin", "typ": "access",
        "jti": str(uuid.uuid4()), "iat": now, "exp": now + 60,
        "iss": SETTINGS.jwt_issuer, "aud": SETTINGS.jwt_audience,
    }  # fmt: skip
    claims.update(over)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, SETTINGS.jwt_secret, algorithm="HS256"), claims


# ----------------------------------------------------------------- Backoff
def test_backoff_ussel_artar_tavanda_durur_ve_sifirlanir():
    b = Backoff(base=1, max_delay=8)
    delays = [b.next_delay() for _ in range(6)]
    assert 0.8 <= delays[0] <= 1.2
    assert 3.2 <= delays[2] <= 4.8
    assert all(d <= 8 * 1.2 for d in delays)
    b.reset()
    assert b.next_delay() <= 1.2


# ----------------------------------------------------------------- Cache
def test_cache_aside_ve_namespace_invalidation():
    cache = RedisCache(fakeredis.FakeRedis(decode_responses=True), "t")
    calls = []

    def loader():
        calls.append(1)
        return {"n": len(calls)}

    assert cache.get_or_load("posts", "k", 60, loader) == {"n": 1}
    assert cache.get_or_load("posts", "k", 60, loader) == {"n": 1}  # cache'ten
    cache.bump("posts")  # tüm 'posts' anahtarları O(1) geçersiz
    assert cache.get_or_load("posts", "k", 60, loader) == {"n": 2}


def test_cache_redis_coktugunde_fail_open():
    class Broken:
        def __getattr__(self, _):
            def fail(*a, **k):
                raise redis.ConnectionError("down")

            return fail

    cache = RedisCache(Broken(), "t")
    assert cache.get_or_load("posts", "k", 60, lambda: "db") == "db"
    cache.bump("posts")  # istisna fırlatmamalı


# ----------------------------------------------------------------- Messaging
def test_envelope_sozlesmesi_ve_correlation():
    token = set_correlation_id("req-123")
    try:
        env = build_envelope(DomainEvent("post.published", {"post_id": "p1"}), "post-service")
    finally:
        reset_correlation_id(token)
    assert set(env) == {"event_id", "event_type", "version", "occurred_at", "source", "correlation_id", "payload"}
    assert env["event_type"] == "post.published"
    assert env["correlation_id"] == "req-123"
    assert env["occurred_at"].endswith("Z")


def test_topoloji_her_kuyruk_icin_sozlesme():
    # Bir servisin kendi yayınladığı event'i tüketmemesi (döngü yok) ve activity-worker'ın her şeyi görmesi
    assert QUEUES["activity-worker.all-events"] == ["#"]
    assert not any(k.startswith("post.") for k in QUEUES["post-service.comment-events"])
    assert not any(k.startswith("comment.") for k in QUEUES["comment-service.post-events"])


# ----------------------------------------------------------------- Security
def test_gecerli_token_principal_uretir():
    tok, claims = _token()
    p = JwtVerifier(SETTINGS).verify(tok)
    assert p.user_id == "u1" and p.is_admin and p.jti == claims["jti"]
    assert ensure_admin(p) is p


@pytest.mark.parametrize(
    ("override", "code"),
    [
        ({"exp": int(time.time()) - 120}, "token_expired"),
        ({"aud": "baska-api"}, "invalid_token"),
        ({"iss": "sahte"}, "invalid_token"),
        ({"typ": "refresh"}, "invalid_token"),
        ({"jti": None}, "invalid_token"),
    ],
)
def test_gecersiz_tokenlar_reddedilir(override, code):
    tok, _ = _token(**override)
    with pytest.raises(UnauthorizedError) as exc:
        JwtVerifier(SETTINGS).verify(tok)
    assert exc.value.code == code


def test_yanlis_anahtarla_imzalanmis_token():
    tok = jwt.encode({"sub": "x"}, "baska-bir-anahtar-32-karakterden-uzun!!", algorithm="HS256")
    with pytest.raises(UnauthorizedError):
        JwtVerifier(SETTINGS).verify(tok)


def test_iptal_edilmis_jti_reddedilir():
    r = fakeredis.FakeRedis(decode_responses=True)
    tok, claims = _token()
    r.set(REVOKED_JTI_KEY.format(jti=claims["jti"]), "1")
    with pytest.raises(UnauthorizedError) as exc:
        JwtVerifier(SETTINGS, r).verify(tok)
    assert exc.value.code == "token_revoked"


def test_reader_rolu_admin_ucuna_giremez():
    tok, _ = _token(role="reader")
    with pytest.raises(ForbiddenError):
        ensure_admin(JwtVerifier(SETTINGS).verify(tok))
