"""Unit of Work: tek transaction, domain event'lerin outbox'a atomik yazımı ve commit sonrası hook'lar."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from ..domain import AggregateRoot
from ..messaging.envelope import build_envelope

log = logging.getLogger(__name__)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker, outbox_model: Any | None, source: str) -> None:
        self._session_factory = session_factory
        self._outbox_model = outbox_model
        self._source = source
        self.session: Session
        self._seen: list[AggregateRoot] = []
        self._after_commit: list[Callable[[], None]] = []

    def __enter__(self):
        self.session = self._session_factory()
        self._seen = []
        self._after_commit = []
        self._init_repositories()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None:
                self.session.rollback()
        finally:
            self.session.close()

    def _init_repositories(self) -> None:  # alt sınıflar override eder
        pass

    def track(self, aggregate: AggregateRoot) -> None:
        if all(a is not aggregate for a in self._seen):
            self._seen.append(aggregate)

    def on_commit(self, callback: Callable[[], None]) -> None:
        self._after_commit.append(callback)

    def commit(self) -> None:
        if self._outbox_model is not None:
            for aggregate in self._seen:
                for event in aggregate.pull_events():
                    envelope = build_envelope(event, source=self._source)
                    self.session.add(
                        self._outbox_model(
                            event_id=event.event_id,
                            event_type=event.name,
                            payload=json.dumps(envelope, ensure_ascii=False),
                            occurred_at=event.occurred_at,
                            attempts=0,
                        )
                    )
        self.session.commit()
        callbacks, self._after_commit = self._after_commit, []
        for cb in callbacks:
            try:
                cb()
            except Exception:  # noqa: BLE001 - commit sonrası hook'lar işlemi bozmamalı
                log.exception("after-commit hook başarısız")

    def rollback(self) -> None:
        self.session.rollback()
