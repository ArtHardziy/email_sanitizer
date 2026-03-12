from __future__ import annotations

from dataclasses import dataclass, field

from runtime_config import MailboxRuntime


@dataclass(slots=True)
class MultiMailboxRuntime:
    user_id: str
    mailboxes: list[MailboxRuntime] = field(default_factory=list)

    def enabled_mailboxes(self) -> list[MailboxRuntime]:
        return [runtime for runtime in self.mailboxes if runtime.mailbox.enabled]

    def get_mailbox(self, mailbox_name: str) -> MailboxRuntime | None:
        for runtime in self.mailboxes:
            if runtime.mailbox.name == mailbox_name:
                return runtime
        return None

    def mailbox_names(self) -> list[str]:
        return [runtime.mailbox.name for runtime in self.mailboxes]
