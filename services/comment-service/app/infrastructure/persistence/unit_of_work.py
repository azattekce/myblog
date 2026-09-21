from devblog_common.persistence import SqlAlchemyUnitOfWork

from .models import OutboxMessage
from .repositories import SqlAlchemyCommentRepository, SqlAlchemyKnownPostRepository


class SqlAlchemyCommentUnitOfWork(SqlAlchemyUnitOfWork):
    def __init__(self, session_factory) -> None:
        super().__init__(session_factory, OutboxMessage, source="comment-service")

    def _init_repositories(self) -> None:
        self.comments = SqlAlchemyCommentRepository(self.session, self.track)
        self.known_posts = SqlAlchemyKnownPostRepository(self.session)
