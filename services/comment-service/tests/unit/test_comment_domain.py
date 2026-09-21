import pytest

from app.domain.comment import Comment, CommentStatus
from devblog_common.domain import BusinessRuleViolation


def _c():
    return Comment.submit("p" * 36, "Ayşe", "Harika yazı!", None, "hash")


def test_submit_is_pending_and_emits_created():
    c = _c()
    assert c.status == CommentStatus.PENDING
    assert [e.name for e in c.pull_events()] == ["comment.created"]


def test_approve_then_reject_adjusts_count():
    c = _c()
    c.pull_events()
    c.approve(current_approved_count=2)
    assert c.pull_events()[0].payload["approved_comment_count"] == 3
    c.reject(current_approved_count=3)
    assert c.pull_events()[0].payload["approved_comment_count"] == 2


def test_invalid_input():
    with pytest.raises(BusinessRuleViolation):
        Comment.submit("p", "A", "ok ok", None, None)
    with pytest.raises(BusinessRuleViolation):
        Comment.submit("p", "Ali", "x", None, None)
