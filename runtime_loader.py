from __future__ import annotations

from pathlib import Path

from config_loader import load_app_config
from mailbox_rules import SenderDomainRules
from runtime_config import MailboxRuntime, build_runtime
from secrets_config import MailboxSecrets


def load_runtimes_from_config(
    config_path: str | Path,
    *,
    state_dir: str | Path = ".state/email_sanitizer",
    default_secrets: MailboxSecrets | None = None,
    default_rules: SenderDomainRules | None = None,
) -> list[MailboxRuntime]:
    app_config = load_app_config(config_path)
    runtimes: list[MailboxRuntime] = []
    for mailbox in app_config.mailboxes:
        if not mailbox.enabled:
            continue
        runtimes.append(
            build_runtime(
                mailbox,
                secrets=default_secrets or MailboxSecrets(),
                rules=default_rules or SenderDomainRules(),
                state_dir=state_dir,
            )
        )
    return runtimes
