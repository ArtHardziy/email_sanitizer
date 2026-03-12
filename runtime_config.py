from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import MailboxConfig
from mailbox_rules import SenderDomainRules
from secrets_config import MailboxSecrets
from state_store import JsonStateStore


@dataclass(slots=True)
class MailboxRuntime:
    mailbox: MailboxConfig
    secrets: MailboxSecrets
    rules: SenderDomainRules
    state_store: JsonStateStore


def build_runtime(
    mailbox: MailboxConfig,
    *,
    secrets: MailboxSecrets | None = None,
    rules: SenderDomainRules | None = None,
    state_dir: str | Path = ".state/email_sanitizer",
) -> MailboxRuntime:
    state_path = Path(state_dir) / f"{mailbox.name}.json"
    return MailboxRuntime(
        mailbox=mailbox,
        secrets=secrets or MailboxSecrets(),
        rules=rules or SenderDomainRules(),
        state_store=JsonStateStore(state_path),
    )
