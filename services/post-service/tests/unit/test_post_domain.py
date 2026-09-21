import pytest

from app.domain.post import Post, PostStatus
from app.domain.value_objects import normalize_tags, reading_time_minutes, slugify
from devblog_common.domain import BusinessRuleViolation


def _post(**kw):
    data = dict(title="Merhaba Dünya", summary="özet", content="İçerik " * 10, author_id="a", author_name="A")
    data.update(kw)
    return Post.create(**data)


def test_slugify_turkish():
    assert slugify("Çalışan Şeyler: Ğüzel İş") == "calisan-seyler-guzel-is"
    assert slugify("C# ve C++") == "csharp-ve-cplusplus"


def test_normalize_tags_dedup_and_limit():
    assert normalize_tags(["Python", "python", " FastAPI "]) == ["python", "fastapi"]
    assert len(normalize_tags([f"t{i}" for i in range(20)])) == 10


def test_reading_time():
    assert reading_time_minutes("kelime " * 400) == 2
    assert reading_time_minutes("kısa") == 1


def test_publish_flow_emits_events():
    post = _post()
    assert post.status == PostStatus.DRAFT
    post.publish()
    assert post.published_at is not None
    names = [e.name for e in post.pull_events()]
    assert names == ["post.created", "post.published"]
    with pytest.raises(BusinessRuleViolation):
        post.publish()


def test_validation():
    with pytest.raises(BusinessRuleViolation):
        _post(title="x")
