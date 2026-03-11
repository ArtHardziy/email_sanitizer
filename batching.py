from __future__ import annotations

from collections import defaultdict

from importance_classifier import ImportanceLevel
from notifier import NotificationMessage


def batch_notifications(messages: list[NotificationMessage]) -> list[str]:
    grouped: dict[str, list[NotificationMessage]] = defaultdict(list)
    for message in messages:
        grouped[message.importance.value].append(message)

    ordered_levels = [
        ImportanceLevel.CRITICAL.value,
        ImportanceLevel.HIGH.value,
        ImportanceLevel.MEDIUM.value,
        ImportanceLevel.LOW.value,
    ]

    batches: list[str] = []
    for level in ordered_levels:
        items = grouped.get(level, [])
        if not items:
            continue
        lines = [f"{len(items)} уведомл. уровня {level}:"]
        for item in items:
            lines.append(f"- {item.title}: {item.body}")
        batches.append("\n".join(lines))
    return batches
