import json

POST = {
    "title": "FastAPI ile Clean Architecture",
    "summary": "Katmanlı mimari üzerine notlar",
    "content": "# Başlık\n\nBu bir **markdown** içeriğidir. " * 5,
    "tags": ["Python", "FastAPI"],
}


def test_admin_endpoints_require_auth(client, reader_headers):
    assert client.post("/api/posts/admin/posts", json=POST).status_code == 401
    assert client.post("/api/posts/admin/posts", json=POST, headers=reader_headers).status_code == 403


def test_full_post_lifecycle(client, admin_headers):
    cat = client.post("/api/posts/admin/categories", json={"name": "Mimari"}, headers=admin_headers)
    assert cat.status_code == 201, cat.text
    res = client.post("/api/posts/admin/posts", json={**POST, "category_id": cat.json()["id"]}, headers=admin_headers)
    assert res.status_code == 201, res.text
    post_id = res.json()["id"]

    # taslak herkese açık listede görünmez
    assert client.get("/api/posts").json()["total"] == 0

    assert client.post(f"/api/posts/admin/posts/{post_id}/publish", headers=admin_headers).status_code == 204
    listing = client.get("/api/posts").json()
    assert listing["total"] == 1
    item = listing["items"][0]
    assert item["slug"] == "fastapi-ile-clean-architecture"
    assert item["tags"] == ["fastapi", "python"]
    assert item["category"]["name"] == "Mimari"

    detail = client.get(f"/api/posts/slug/{item['slug']}").json()
    assert detail["view_count"] == 1 and "markdown" in detail["content"]
    assert client.get("/api/posts?tag=python").json()["total"] == 1
    assert client.get("/api/posts?category=mimari").json()["total"] == 1
    assert client.get("/api/posts?q=clean").json()["total"] == 1
    assert client.get("/api/posts/tags").json()[0]["count"] == 1
    assert client.get("/api/posts/categories").json()[0]["post_count"] == 1

    # güncelleme cache'i geçersiz kılar
    upd = {**POST, "title": "Yeni Başlık", "slug": "yeni-baslik", "category_id": cat.json()["id"]}
    assert client.put(f"/api/posts/admin/posts/{post_id}", json=upd, headers=admin_headers).status_code == 204
    assert client.get("/api/posts").json()["items"][0]["title"] == "Yeni Başlık"

    stats = client.get("/api/posts/admin/stats", headers=admin_headers).json()
    assert stats == {"total": 1, "published": 1, "drafts": 0, "comments": 0}

    # comment-service event'i ile sayaç senkronizasyonu (integration handler)
    from app.application.integration_handlers import CommentEventsHandler

    CommentEventsHandler(client.app_container.commands)(
        {"event_type": "comment.approved", "payload": {"post_id": post_id, "approved_comment_count": 3}}
    )
    assert client.get("/api/posts").json()["items"][0]["comment_count"] == 3

    # kategori kullanımdayken silinemez
    assert client.delete(f"/api/posts/admin/categories/{cat.json()['id']}", headers=admin_headers).status_code == 409
    assert client.delete(f"/api/posts/admin/posts/{post_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/posts/slug/{item['slug']}").status_code == 404


def test_duplicate_slug_gets_suffix(client, admin_headers):
    a = client.post("/api/posts/admin/posts", json={**POST, "publish": True}, headers=admin_headers).json()["id"]
    b = client.post("/api/posts/admin/posts", json={**POST, "publish": True}, headers=admin_headers).json()["id"]
    sa = client.get(f"/api/posts/admin/posts/{a}", headers=admin_headers).json()["slug"]
    sb = client.get(f"/api/posts/admin/posts/{b}", headers=admin_headers).json()["slug"]
    assert sa != sb and sb.endswith("-2")


def test_outbox_records_events(client, admin_headers):
    from sqlalchemy import select

    from app.infrastructure.persistence.models import OutboxMessage

    client.post("/api/posts/admin/posts", json={**POST, "publish": True}, headers=admin_headers)
    with client.app_container.engine.connect() as conn:
        rows = conn.execute(select(OutboxMessage.event_type, OutboxMessage.payload)).all()
    types = [r[0] for r in rows]
    assert types == ["post.created", "post.published"]
    envelope = json.loads(rows[1][1])
    assert envelope["source"] == "post-service" and envelope["payload"]["status"] == "published"
