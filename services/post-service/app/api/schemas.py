from pydantic import BaseModel, Field, HttpUrl, field_validator


class PostWriteRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    summary: str = Field(default="", max_length=500)
    content: str = Field(min_length=10, max_length=200_000)
    slug: str | None = Field(default=None, max_length=180)
    category_id: str | None = Field(default=None, max_length=36)
    tags: list[str] = Field(default_factory=list, max_length=10)
    cover_image_url: HttpUrl | None = None

    @field_validator("slug", "category_id", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return v or None


class CreatePostRequest(PostWriteRequest):
    publish: bool = False


class CategoryRequest(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    description: str = Field(default="", max_length=300)
    image_url: HttpUrl | None = None


class IdResponse(BaseModel):
    id: str
