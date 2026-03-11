from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from notifier import NotificationMessage


@dataclass(slots=True)
class DedupState:
    seen_hashes: set[str] = field(default_factory=set)


def notification_fingerprint(message: NotificationMessage) -> str:
    payload = f"{message.title}\n{message.body}\n{message.importance.value}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def deduplicate_notifications(messages: list[NotificationMessage], state: DedupState | None = None) -> tuple[list[NotificationMessage], DedupState]:
    state = state or DedupState()
    fresh: list[NotificationMessage] = []
    for message in messages:
        fp = notification_fingerprint(message)
        if fp in state.seen_hashes:
            continue
        state.seen_hashes.add(fp)
        fresh.append(message)
    return fresh, state
