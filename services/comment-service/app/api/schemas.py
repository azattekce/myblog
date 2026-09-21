from pydantic import BaseModel, Field


class SubmitCommentRequest(BaseModel):
    post_id: str = Field(min_length=36, max_length=36)
    author_name: str = Field(min_length=2, max_length=60)
    author_email: str | None = Field(default=None, max_length=254)
    content: str = Field(min_length=3, max_length=2000)
    website: str | None = Field(default=None, max_length=200, description="Honeypot alanı; boş bırakılmalı")


class SubmitCommentResponse(BaseModel):
    id: str
    status: str = "pending"
    message: str = "Yorumunuz alındı, onaylandıktan sonra yayınlanacak."
