from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import get_container
from app.container import Container

router = APIRouter(prefix="/api/posts", tags=["posts (public)"])


@router.get("")
def list_posts(
    response: Response,
    page: int = Query(1, ge=1, le=1000),
    size: int = Query(10, ge=1, le=50),
    tag: str | None = Query(None, max_length=30),
    category: str | None = Query(None, max_length=80),
    q: str | None = Query(None, max_length=100),
    c: Container = Depends(get_container),
):
    response.headers["Cache-Control"] = "public, max-age=30"
    return c.queries.list_published(page, size, tag, category, q)


@router.get("/tags")
def tags(c: Container = Depends(get_container)):
    return c.queries.tags()


@router.get("/categories")
def categories(c: Container = Depends(get_container)):
    return c.queries.categories()


@router.get("/slug/{slug}")
def get_by_slug(slug: str, c: Container = Depends(get_container)):
    return c.queries.get_published(slug)
