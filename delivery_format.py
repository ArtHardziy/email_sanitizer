from __future__ import annotations

from dataclasses import dataclass

from notifier import NotificationMessage


@dataclass(slots=True)
class DeliveryPayload:
    title: str
    body: str
    importance: str
    channel_hint: str = "telegram"


def to_delivery_payload(message: NotificationMessage, *, channel_hint: str = "telegram") -> DeliveryPayload:
    return DeliveryPayload(
        title=message.title,
        body=message.body,
        importance=message.importance.value,
        channel_hint=channel_hint,
    )


def render_plaintext(message: NotificationMessage) -> str:
    return f"{message.title}\n{message.body}"
