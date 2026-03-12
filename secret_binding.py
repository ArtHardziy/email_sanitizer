from __future__ import annotations

from dataclasses import dataclass

from config import MailboxConfig
from secrets_config import MailboxSecrets


@dataclass(slots=True)
class BoundMailboxSecrets:
    mailbox_name: str
    resolved_secret: str | None


def bind_mailbox_secret(mailbox: MailboxConfig, secrets: MailboxSecrets) -> BoundMailboxSecrets:
    return BoundMailboxSecrets(
        mailbox_name=mailbox.name,
        resolved_secret=secrets.resolve_secret(),
    )
