from batching import batch_notifications
from dedup import deduplicate_notifications
from importance_classifier import ImportanceLevel
from notifier import NotificationMessage


def test_deduplicate_notifications() -> None:
    messages = [
        NotificationMessage(title="A", body="body", importance=ImportanceLevel.HIGH),
        NotificationMessage(title="A", body="body", importance=ImportanceLevel.HIGH),
    ]
    fresh, _ = deduplicate_notifications(messages)
    assert len(fresh) == 1


def test_batch_notifications() -> None:
    messages = [
        NotificationMessage(title="A", body="body1", importance=ImportanceLevel.CRITICAL),
        NotificationMessage(title="B", body="body2", importance=ImportanceLevel.HIGH),
    ]
    batches = batch_notifications(messages)
    assert len(batches) == 2
    assert "critical" in batches[0]


def run_tests() -> None:
    tests = [test_deduplicate_notifications, test_batch_notifications]
    for test in tests:
        test()
    print(f"ok: {len(tests)} dedup/batching tests passed")


if __name__ == "__main__":
    run_tests()
