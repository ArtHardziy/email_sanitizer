from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from importance_classifier import ImportanceLevel, ImportancePolicy
from models import SanitizerPolicy
from policy_profiles import balanced_policy


@dataclass(slots=True)
class MailboxConfig:
    name: str
    provider: str = "imap"
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    folder: str = "INBOX"
    use_ssl: bool = True
    policy: SanitizerPolicy = field(default_factory=balanced_policy)
    importance_policy: ImportancePolicy = field(default_factory=ImportancePolicy)
    notify_min_level: ImportanceLevel = ImportanceLevel.HIGH
    enabled: bool = True


@dataclass(slots=True)
class AppConfig:
    mailboxes: list[MailboxConfig] = field(default_factory=list)


def default_app_config() -> AppConfig:
    return AppConfig(mailboxes=[])
