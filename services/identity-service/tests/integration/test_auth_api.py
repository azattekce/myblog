CSRF = {"X-CSRF-Protection": "1"}


def _login(client, password="Admin123!"):
    return client.post("/api/identity/auth/login", json={"username": "admin", "password": password})


def test_health(client):
    assert client.get("/health/live").status_code == 200
    ready = client.get("/health/ready")
    assert ready.status_code == 200, ready.text


def test_login_me_refresh_logout_flow(client):
    res = _login(client)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["user"]["role"] == "admin"
    assert "devblog_rt" in res.cookies
    token = body["access_token"]

    me = client.get("/api/identity/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["username"] == "admin"

    # refresh CSRF başlığı olmadan reddedilir
    assert client.post("/api/identity/auth/refresh").status_code == 403

    old_cookie = client.cookies.get("devblog_rt")
    ref = client.post("/api/identity/auth/refresh", headers=CSRF)
    assert ref.status_code == 200, ref.text
    assert client.cookies.get("devblog_rt") != old_cookie

    out = client.post("/api/identity/auth/logout", headers={**CSRF, "Authorization": f"Bearer {token}"})
    assert out.status_code == 204
    # iptal edilmiş access token artık kullanılamaz
    assert client.get("/api/identity/users/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_refresh_token_reuse_revokes_family(client):
    _login(client)
    stolen = client.cookies.get("devblog_rt")
    assert client.post("/api/identity/auth/refresh", headers=CSRF).status_code == 200
    # saldırgan eski token'ı tekrar kullanır
    client.cookies.clear()
    client.cookies.set("devblog_rt", stolen, path="/api/identity/auth")
    reuse = client.post("/api/identity/auth/refresh", headers=CSRF)
    assert reuse.status_code == 401
    assert reuse.json()["code"] == "refresh_token_reused"


def test_wrong_password_and_lockout(client):
    for _ in range(5):
        assert _login(client, "wrong").status_code == 401
    locked = _login(client, "Admin123!")
    assert locked.status_code == 429
    assert locked.headers["content-type"].startswith("application/problem+json")


def test_validation_error_is_problem_json(client):
    res = client.post("/api/identity/auth/login", json={"username": "a"})
    assert res.status_code == 422
    assert res.json()["code"] == "validation_error"
