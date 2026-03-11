from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Sequence

from models import AllowedView, RiskFlag, SanitizedEmail


class ImportanceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(slots=True)
class ImportancePolicy:
    priority_senders: set[str] = field(default_factory=set)
    priority_domains: set[str] = field(default_factory=set)
    noisy_senders: set[str] = field(default_factory=set)
    notify_on_medical: bool = True
    notify_on_financial: bool = True
    notify_on_security: bool = True
    notify_on_blocked_sensitive: bool = True


SECURITY_FLAGS = {
    RiskFlag.PROMPT_INJECTION,
    RiskFlag.TOOL_INVOCATION_ATTEMPT,
    RiskFlag.CREDENTIAL_REQUEST,
    RiskFlag.OTP_PRESENT,
    RiskFlag.AUTH_LINK_PRESENT,
    RiskFlag.TOKEN_PRESENT,
    RiskFlag.SOCIAL_ENGINEERING_TONE,
    RiskFlag.UNEXPECTED_URGENCY,
    RiskFlag.SUSPICIOUS_URL,
}


def classify_importance(email: SanitizedEmail, policy: ImportancePolicy | None = None) -> ImportanceLevel:
    policy = policy or ImportancePolicy()
    sender = email.sender.lower()
    domain = sender.split("@", 1)[1] if "@" in sender else ""
    flags = set(email.risk_flags)

    if sender in policy.noisy_senders:
        return ImportanceLevel.LOW

    if email.allowed_view == AllowedView.BLOCK_AND_NOTIFY and policy.notify_on_blocked_sensitive:
        return ImportanceLevel.CRITICAL

    if flags & SECURITY_FLAGS and policy.notify_on_security:
        return ImportanceLevel.CRITICAL

    if RiskFlag.MEDICAL_CONTENT in flags and policy.notify_on_medical:
        return ImportanceLevel.HIGH

    if RiskFlag.FINANCIAL_CONTENT in flags and policy.notify_on_financial:
        return ImportanceLevel.HIGH

    if sender in policy.priority_senders or domain in policy.priority_domains:
        return ImportanceLevel.HIGH

    if email.allowed_view in {AllowedView.METADATA_ONLY, AllowedView.SUMMARY_ONLY}:
        return ImportanceLevel.MEDIUM

    return ImportanceLevel.LOW


def should_notify(level: ImportanceLevel, *, min_level: ImportanceLevel = ImportanceLevel.HIGH) -> bool:
    order = {
        ImportanceLevel.LOW: 0,
        ImportanceLevel.MEDIUM: 1,
        ImportanceLevel.HIGH: 2,
        ImportanceLevel.CRITICAL: 3,
    }
    return order[level] >= order[min_level]
