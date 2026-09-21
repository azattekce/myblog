from app.handlers import EVENTS_CONSUMED, ActivityHandler


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def notify(self, subject, body):
        self.sent.append(subject)


def test_comment_created_triggers_notification():
    n = FakeNotifier()
    ActivityHandler(n)(
        {"event_type": "comment.created", "source": "comment-service", "payload": {"author_name": "A", "post_id": "p"}}
    )
    assert n.sent == ["Moderasyon bekleyen yeni yorum"]
    assert EVENTS_CONSUMED.labels("comment.created", "comment-service")._value.get() == 1


def test_unknown_event_is_only_logged():
    n = FakeNotifier()
    ActivityHandler(n)({"event_type": "post.updated", "payload": {}})
    assert n.sent == []
