from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from onboarding_models import ConnectedMailbox, MailboxState


class MailboxRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _normalize_mailbox(self, item: dict[str, object]) -> ConnectedMailbox:
        normalized = dict(item)
        normalized["state"] = MailboxState(normalized["state"])
        return ConnectedMailbox(**normalized)

    def _load_all(self) -> dict[str, ConnectedMailbox]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        mailboxes: dict[str, ConnectedMailbox] = {}
        for item in raw.get("mailboxes", []):
            mailbox = self._normalize_mailbox(item)
            mailboxes[mailbox.mailbox_id] = mailbox
        return mailboxes

    def _save_all(self, mailboxes: dict[str, ConnectedMailbox]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"mailboxes": [asdict(v) for v in mailboxes.values()]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def put(self, mailbox: ConnectedMailbox) -> None:
        mailboxes = self._load_all()
        mailboxes[mailbox.mailbox_id] = mailbox
        self._save_all(mailboxes)

    def get(self, mailbox_id: str) -> ConnectedMailbox | None:
        return self._load_all().get(mailbox_id)

    def list_all(self) -> list[ConnectedMailbox]:
        return list(self._load_all().values())

    def list_for_user(self, user_id: str) -> list[ConnectedMailbox]:
        return [mailbox for mailbox in self._load_all().values() if mailbox.user_id == user_id]
