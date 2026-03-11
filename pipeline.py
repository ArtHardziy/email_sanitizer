from __future__ import annotations

from dataclasses import dataclass

from config import MailboxConfig
from importance_classifier import classify_importance, should_notify
from integration import ProcessedMailRecord, process_mail_records
from mailbox_rules import SenderDomainRules
from notifier import NotificationMessage, build_notification
from models import SanitizedEmail


@dataclass(slots=True)
class PipelineResult:
    processed: list[ProcessedMailRecord]
    notifications: list[NotificationMessage]


def run_mailbox_pipeline(records, mailbox: MailboxConfig, rules: SenderDomainRules | None = None) -> PipelineResult:
    rules = rules or SenderDomainRules()
    processed = process_mail_records(records, policy=mailbox.policy)
    notifications: list[NotificationMessage] = []

    for record in processed:
        sender = record.sanitized.sender
        if rules.is_denied(sender):
            continue

        importance = classify_importance(record.sanitized, mailbox.importance_policy)
        if rules.is_explicitly_allowed(sender) and importance.value in {"low", "medium"}:
            # Allowed senders can still be escalated by mailbox-specific preference.
            importance = mailbox.notify_min_level if mailbox.notify_min_level.value in {"high", "critical"} else importance

        if should_notify(importance, min_level=mailbox.notify_min_level):
            notifications.append(build_notification(record.sanitized, importance))

    return PipelineResult(processed=processed, notifications=notifications)
