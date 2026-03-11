from __future__ import annotations

import re

from action_classifier import classify_actions
from extractors import extract_facts
from models import AllowedView, RawEmail, RiskFlag


SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.!?])\s+")
NOISY_SENTENCE_RE = re.compile(r"(unsubscribe|privacy policy|view in browser|terms of service)", re.IGNORECASE)


def build_content_aware_summary(email: RawEmail, flags: list[RiskFlag], allowed_view: AllowedView, sanitized_text: str | None) -> str:
    if allowed_view == AllowedView.BLOCK_AND_NOTIFY:
        return f"Получено потенциально чувствительное письмо от {email.sender}. Содержимое заблокировано политикой безопасности."
    if allowed_view == AllowedView.METADATA_ONLY:
        return f"Получено письмо от {email.sender} с ограниченным доступом. Доступны только метаданные из-за чувствительного содержимого."

    basis = sanitized_text or email.snippet or email.subject
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(basis) if s.strip()]
    useful = [s for s in sentences if not NOISY_SENTENCE_RE.search(s)]
    chosen = useful[:2] if useful else [email.subject]
    text = " ".join(chosen).strip()
    facts = extract_facts(text)
    actions = classify_actions(text)

    extras: list[str] = []
    if facts.action_items:
        extras.append("Действия: " + " | ".join(facts.action_items[:2]))
    if actions.kinds:
        extras.append("Типы действий: " + ", ".join(kind.value for kind in actions.kinds[:3]))
    if facts.date_mentions:
        extras.append("Даты/время: " + ", ".join(facts.date_mentions[:3]))

    if flags and allowed_view == AllowedView.SUMMARY_ONLY:
        labels = ", ".join(flag.value for flag in flags)
        extras.append(f"Флаги риска: {labels}")

    return (text + (" " + " ".join(extras) if extras else "")).strip()
