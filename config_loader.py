from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import AppConfig, MailboxConfig
from importance_classifier import ImportanceLevel, ImportancePolicy
from policy_profiles import balanced_policy, privacy_max_policy, strict_policy, work_heavy_policy


PROFILE_MAP = {
    "strict": strict_policy,
    "balanced": balanced_policy,
    "work-heavy": work_heavy_policy,
    "privacy-max": privacy_max_policy,
}

IMPORTANCE_MAP = {
    "low": ImportanceLevel.LOW,
    "medium": ImportanceLevel.MEDIUM,
    "high": ImportanceLevel.HIGH,
    "critical": ImportanceLevel.CRITICAL,
}


def load_app_config(path: str | Path) -> AppConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    mailboxes = [parse_mailbox(item) for item in raw.get("mailboxes", [])]
    return AppConfig(mailboxes=mailboxes)


def parse_mailbox(data: dict[str, Any]) -> MailboxConfig:
    profile_name = data.get("policyProfile", "balanced")
    policy_factory = PROFILE_MAP.get(profile_name, balanced_policy)
    importance = data.get("importancePolicy", {})

    return MailboxConfig(
        name=data["name"],
        provider=data.get("provider", "imap"),
        host=data.get("host"),
        port=data.get("port"),
        username=data.get("username"),
        folder=data.get("folder", "INBOX"),
        use_ssl=data.get("useSsl", True),
        policy=policy_factory(),
        importance_policy=ImportancePolicy(
            priority_senders=set(importance.get("prioritySenders", [])),
            priority_domains=set(importance.get("priorityDomains", [])),
            noisy_senders=set(importance.get("noisySenders", [])),
            notify_on_medical=importance.get("notifyOnMedical", True),
            notify_on_financial=importance.get("notifyOnFinancial", True),
            notify_on_security=importance.get("notifyOnSecurity", True),
            notify_on_blocked_sensitive=importance.get("notifyOnBlockedSensitive", True),
        ),
        notify_min_level=IMPORTANCE_MAP.get(data.get("notifyMinLevel", "high"), ImportanceLevel.HIGH),
        enabled=data.get("enabled", True),
    )
