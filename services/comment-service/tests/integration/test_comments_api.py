import uuid

POST_ID = str(uuid.uuid4())


def _publish_post(client, published=True):
    client.app_container.post_events(
        {
            "event_type": "post.published" if published else "post.unpublished",
            "payload": {
                "post_id": POST_ID,
                "slug": "yazi",
                "title": "Yazı",
                "status": "published" if published else "draft",
            },
        }
    )


def _comment(client, **kw):
    body = {"post_id": POST_ID, "author_name": "Ayşe", "content": "Çok faydalı bir yazı olmuş."}
    body.update(kw)
    return client.post("/api/comments", json=body)


def test_comment_requires_known_published_post(client):
    assert _comment(client).status_code == 404
    _publish_post(client)
    assert _comment(client).status_code == 202


def test_moderation_flow(client, admin_headers):
    _publish_post(client)
    cid = _comment(client).json()["id"]
    assert client.get(f"/api/comments/post/{POST_ID}").json() == []

    pending = client.get("/api/comments/admin?status=pending", headers=admin_headers).json()
    assert pending["total"] == 1 and pending["items"][0]["post_title"] == "Yazı"

    assert client.post(f"/api/comments/admin/{cid}/approve", headers=admin_headers).status_code == 204
    approved = client.get(f"/api/comments/post/{POST_ID}").json()
    assert len(approved) == 1 and approved[0]["author_name"] == "Ayşe"
    assert client.get("/api/comments/admin/counts", headers=admin_headers).json()["approved"] == 1

    assert client.delete(f"/api/comments/admin/{cid}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/comments/post/{POST_ID}").json() == []


def test_honeypot_and_rate_limit(client):
    _publish_post(client)
    assert _comment(client, website="http://spam").status_code == 422
    codes = [_comment(client).status_code for _ in range(6)]
    assert codes[-1] == 429


def test_post_deleted_cleans_comments(client, admin_headers):
    _publish_post(client)
    _comment(client)
    client.app_container.post_events({"event_type": "post.deleted", "payload": {"post_id": POST_ID}})
    assert client.get("/api/comments/admin", headers=admin_headers).json()["total"] == 0
    assert _comment(client).status_code == 404
