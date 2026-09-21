from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.dependencies import get_container, require_admin
from app.api.schemas import SubmitCommentRequest, SubmitCommentResponse
from app.application.handlers import SubmitCommentCommand
from app.container import Container

public = APIRouter(prefix="/api/comments", tags=["comments (public)"])
admin = APIRouter(prefix="/api/comments/admin", tags=["comments (admin)"], dependencies=[Depends(require_admin)])


@public.get("/post/{post_id}")
def approved_for_post(post_id: str, c: Container = Depends(get_container)):
    return c.queries.approved_for_post(post_id)


@public.post("", status_code=status.HTTP_202_ACCEPTED, response_model=SubmitCommentResponse)
def submit(body: SubmitCommentRequest, request: Request, c: Container = Depends(get_container)):
    comment_id = c.commands.submit(
        SubmitCommentCommand(
            post_id=body.post_id,
            author_name=body.author_name,
            content=body.content,
            author_email=body.author_email or None,
            ip=request.client.host if request.client else None,
            honeypot=body.website,
        )
    )
    return SubmitCommentResponse(id=comment_id)


@admin.get("")
def admin_list(
    status_: str | None = Query(None, alias="status", pattern="^(pending|approved|rejected)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    c: Container = Depends(get_container),
):
    return c.queries.admin_list(status_, page, size)


@admin.get("/counts")
def counts(c: Container = Depends(get_container)):
    return c.queries.counts()


@admin.post("/{comment_id}/approve", status_code=status.HTTP_204_NO_CONTENT)
def approve(comment_id: str, c: Container = Depends(get_container)):
    c.commands.approve(comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin.post("/{comment_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
def reject(comment_id: str, c: Container = Depends(get_container)):
    c.commands.reject(comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(comment_id: str, c: Container = Depends(get_container)):
    c.commands.delete(comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
