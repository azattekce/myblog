from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from devblog_common.clock import utcnow
from devblog_common.domain import AggregateRoot, BusinessRuleViolation, ForbiddenError, new_id

_USERNAME = re.compile(r"^[a-zA-Z0-9_.\-]{3,50}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Role(str, Enum):
    ADMIN = "admin"
    READER = "reader"


@dataclass
class User(AggregateRoot):
    id: str
    username: str
    email: str
    display_name: str
    password_hash: str
    role: Role
    is_active: bool = True
    created_at: datetime = field(default_factory=utcnow)
    last_login_at: datetime | None = None

    @classmethod
    def register(cls, username: str, email: str, display_name: str, password_hash: str, role: Role) -> User:
        if not _USERNAME.match(username):
            raise BusinessRuleViolation("Kullanıcı adı 3-50 karakter olmalı (harf, rakam, _ . -)")
        if not _EMAIL.match(email):
            raise BusinessRuleViolation("Geçerli bir e-posta adresi girin")
        user = cls(
            id=new_id(),
            username=username.lower(),
            email=email.lower(),
            display_name=display_name.strip() or username,
            password_hash=password_hash,
            role=role,
        )
        user.record_event("user.registered", {"user_id": user.id, "username": user.username, "role": role.value})
        return user

    def ensure_can_login(self) -> None:
        if not self.is_active:
            raise ForbiddenError("Hesap devre dışı", code="account_disabled")

    def record_login(self, ip: str | None) -> None:
        self.last_login_at = utcnow()
        self.record_event("user.logged_in", {"user_id": self.id, "username": self.username, "ip": ip})

    def change_password_hash(self, new_hash: str) -> None:
        self.password_hash = new_hash
