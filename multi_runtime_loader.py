from __future__ import annotations

from pathlib import Path

from mailbox_rules import SenderDomainRules
from multi_runtime import MultiMailboxRuntime
from runtime_loader import load_runtimes_from_config
from secrets_config import MailboxSecrets


def load_multi_runtime(
    *,
    user_id: str,
    config_path: str | Path,
    state_dir: str | Path = ".state/email_sanitizer",
    default_secrets: MailboxSecrets | None = None,
    default_rules: SenderDomainRules | None = None,
    env_prefix: str | None = None,
) -> MultiMailboxRuntime:
    runtimes = load_runtimes_from_config(
        config_path,
        state_dir=state_dir,
        default_secrets=default_secrets,
        default_rules=default_rules,
        env_prefix=env_prefix,
    )
    return MultiMailboxRuntime(user_id=user_id, mailboxes=runtimes)
