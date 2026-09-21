from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_container, require_admin
from app.api.schemas import CategoryRequest, CreatePostRequest, IdResponse, PostWriteRequest
from app.application.commands.models import CreateCategoryCommand, CreatePostCommand, UpdatePostCommand
from app.container import Container
from devblog_common.web import Principal

router = APIRouter(prefix="/api/posts/admin", tags=["posts (admin)"], dependencies=[Depends(require_admin)])


@router.get("/stats")
def stats(c: Container = Depends(get_container)):
    return c.queries.stats()


@router.get("/posts")
def list_all(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_: str | None = Query(None, alias="status", pattern="^(draft|published)$"),
    q: str | None = Query(None, max_length=100),
    c: Container = Depends(get_container),
):
    return c.queries.admin_list(page, size, status_, q)


@router.get("/posts/{post_id}")
def get_one(post_id: str, c: Container = Depends(get_container)):
    return c.queries.admin_get(post_id)


@router.post("/posts", status_code=status.HTTP_201_CREATED, response_model=IdResponse)
def create(
    body: CreatePostRequest, principal: Principal = Depends(require_admin), c: Container = Depends(get_container)
):
    post_id = c.commands.create(
        CreatePostCommand(
            title=body.title,
            summary=body.summary,
            content=body.content,
            author_id=principal.user_id,
            author_name=principal.display_name or principal.username,
            slug=body.slug,
            category_id=body.category_id,
            tags=body.tags,
            cover_image_url=str(body.cover_image_url) if body.cover_image_url else None,
            publish=body.publish,
        )
    )
    return IdResponse(id=post_id)


@router.put("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def update(post_id: str, body: PostWriteRequest, c: Container = Depends(get_container)):
    c.commands.update(
        UpdatePostCommand(
            post_id=post_id,
            title=body.title,
            summary=body.summary,
            content=body.content,
            slug=body.slug,
            category_id=body.category_id,
            tags=body.tags,
            cover_image_url=str(body.cover_image_url) if body.cover_image_url else None,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/posts/{post_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
def publish(post_id: str, c: Container = Depends(get_container)):
    c.commands.publish(post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/posts/{post_id}/unpublish", status_code=status.HTTP_204_NO_CONTENT)
def unpublish(post_id: str, c: Container = Depends(get_container)):
    c.commands.unpublish(post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(post_id: str, c: Container = Depends(get_container)):
    c.commands.delete(post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/categories", status_code=status.HTTP_201_CREATED, response_model=IdResponse)
def create_category(body: CategoryRequest, c: Container = Depends(get_container)):
    return IdResponse(
        id=c.commands.create_category(
            CreateCategoryCommand(body.name, body.description, str(body.image_url) if body.image_url else None)
        )
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, c: Container = Depends(get_container)):
    c.commands.delete_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
