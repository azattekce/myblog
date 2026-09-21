from devblog_common.persistence import SqlAlchemyUnitOfWork

from .models import OutboxMessage
from .repositories import SqlAlchemyCategoryRepository, SqlAlchemyPostRepository


class SqlAlchemyPostUnitOfWork(SqlAlchemyUnitOfWork):
    def __init__(self, session_factory) -> None:
        super().__init__(session_factory, OutboxMessage, source="post-service")

    def _init_repositories(self) -> None:
        self.posts = SqlAlchemyPostRepository(self.session, self.track)
        self.categories = SqlAlchemyCategoryRepository(self.session)
