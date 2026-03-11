from __future__ import annotations

from dataclasses import dataclass

from importance_classifier import ImportanceLevel
from models import AllowedView, SanitizedEmail


@dataclass(slots=True)
class NotificationMessage:
    title: str
    body: str
    importance: ImportanceLevel


EMOJI = {
    ImportanceLevel.LOW: "ℹ️",
    ImportanceLevel.MEDIUM: "🔹",
    ImportanceLevel.HIGH: "⚠️",
    ImportanceLevel.CRITICAL: "🚨",
}


def build_notification(email: SanitizedEmail, importance: ImportanceLevel) -> NotificationMessage:
    emoji = EMOJI[importance]
    title = f"{emoji} Email alert: {email.sender}"

    if email.allowed_view == AllowedView.BLOCK_AND_NOTIFY:
        body = (
            f"Пришло потенциально чувствительное письмо: {email.subject}. "
            f"Содержимое скрыто политикой безопасности."
        )
    elif email.allowed_view == AllowedView.METADATA_ONLY:
        body = (
            f"Пришло письмо с ограниченным доступом: {email.subject}. "
            f"Доступны только метаданные."
        )
    elif email.allowed_view == AllowedView.SUMMARY_ONLY:
        body = f"{email.subject}. {email.safe_summary}"
    else:
        snippet = email.sanitized_snippet or email.safe_summary
        body = f"{email.subject}. {snippet}"

    return NotificationMessage(title=title, body=body, importance=importance)
