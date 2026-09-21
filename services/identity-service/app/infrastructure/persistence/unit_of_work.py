from devblog_common.persistence import SqlAlchemyUnitOfWork

from .models import OutboxMessage
from .repositories import SqlAlchemyRefreshTokenRepository, SqlAlchemyUserRepository


class SqlAlchemyIdentityUnitOfWork(SqlAlchemyUnitOfWork):
    def __init__(self, session_factory) -> None:
        super().__init__(session_factory, OutboxMessage, source="identity-service")

    def _init_repositories(self) -> None:
        self.users = SqlAlchemyUserRepository(self.session, self.track)
        self.refresh_tokens = SqlAlchemyRefreshTokenRepository(self.session)
