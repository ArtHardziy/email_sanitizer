from __future__ import annotations

from dataclasses import dataclass, field

from notifier import NotificationMessage


@dataclass(slots=True)
class MailboxRunError:
    mailbox_name: str
    code: str
    message: str


@dataclass(slots=True)
class AggregatedMessage:
    provider: str
    mailbox_name: str
    folder: str
    message_id: str
    subject: str
    from_address: str
    date: str
    snippet: str
    flags: dict


@dataclass(slots=True)
class AggregatedRunResult:
    result: str
    mailbox_count: int
    success_count: int
    failure_count: int
    notifications: list[NotificationMessage] = field(default_factory=list)
    messages: list[AggregatedMessage] = field(default_factory=list)
    errors: list[MailboxRunError] = field(default_factory=list)
