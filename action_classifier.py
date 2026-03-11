from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from extractors import extract_facts


class ActionKind(str, Enum):
    REPLY_NEEDED = "reply_needed"
    CALL_NEEDED = "call_needed"
    PAYMENT_NEEDED = "payment_needed"
    REVIEW_NEEDED = "review_needed"
    CONFIRMATION_NEEDED = "confirmation_needed"


@dataclass(slots=True)
class ActionSignals:
    kinds: list[ActionKind] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


def classify_actions(text: str) -> ActionSignals:
    lower = text.lower()
    facts = extract_facts(text)
    signals = ActionSignals(evidence=facts.action_items[:])

    def add(kind: ActionKind) -> None:
        if kind not in signals.kinds:
            signals.kinds.append(kind)

    if any(word in lower for word in ["reply", "ответить", "respond"]):
        add(ActionKind.REPLY_NEEDED)
    if any(word in lower for word in ["call", "позвонить", "phone"]):
        add(ActionKind.CALL_NEEDED)
    if any(word in lower for word in ["pay", "payment", "оплатить", "invoice", "billing"]):
        add(ActionKind.PAYMENT_NEEDED)
    if any(word in lower for word in ["review", "проверь", "посмотри", "approve pr"]):
        add(ActionKind.REVIEW_NEEDED)
    if any(word in lower for word in ["confirm", "подтвердить", "verification", "identity"]):
        add(ActionKind.CONFIRMATION_NEEDED)

    return signals
