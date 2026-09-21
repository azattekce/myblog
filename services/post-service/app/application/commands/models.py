from dataclasses import dataclass, field


@dataclass(frozen=True)
class CreatePostCommand:
    title: str
    summary: str
    content: str
    author_id: str
    author_name: str
    slug: str | None = None
    category_id: str | None = None
    tags: list[str] = field(default_factory=list)
    cover_image_url: str | None = None
    publish: bool = False


@dataclass(frozen=True)
class UpdatePostCommand:
    post_id: str
    title: str
    summary: str
    content: str
    slug: str | None = None
    category_id: str | None = None
    tags: list[str] = field(default_factory=list)
    cover_image_url: str | None = None


@dataclass(frozen=True)
class CreateCategoryCommand:
    name: str
    description: str = ""
    image_url: str | None = None
