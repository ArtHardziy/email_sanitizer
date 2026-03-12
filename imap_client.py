from __future__ import annotations

import imaplib
from dataclasses import dataclass
from typing import Iterable

from config import MailboxConfig


@dataclass(slots=True)
class IMAPSession:
    client: imaplib.IMAP4 | imaplib.IMAP4_SSL
    mailbox: MailboxConfig

    def select_folder(self) -> None:
        status, _ = self.client.select(self.mailbox.folder)
        if status != "OK":
            raise RuntimeError(f"Failed to select folder: {self.mailbox.folder}")

    def search_unseen(self) -> list[bytes]:
        status, data = self.client.search(None, "UNSEEN")
        if status != "OK":
            raise RuntimeError("Failed to search unseen messages")
        if not data or not data[0]:
            return []
        return data[0].split()

    def fetch_rfc822(self, message_id: bytes) -> bytes:
        status, data = self.client.fetch(message_id, "(RFC822)")
        if status != "OK" or not data or not data[0]:
            raise RuntimeError(f"Failed to fetch message {message_id!r}")
        payload = data[0][1]
        return payload if isinstance(payload, bytes) else bytes(payload)

    def mark_seen(self, message_ids: Iterable[bytes]) -> None:
        for message_id in message_ids:
            self.client.store(message_id, "+FLAGS", "\\Seen")

    def logout(self) -> None:
        try:
            self.client.logout()
        except Exception:
            pass


def login_imap(mailbox: MailboxConfig, secret: str) -> IMAPSession:
    client = imaplib.IMAP4_SSL(mailbox.host, mailbox.port or 993) if mailbox.use_ssl else imaplib.IMAP4(mailbox.host, mailbox.port or 143)
    client.login(mailbox.username, secret)
    session = IMAPSession(client=client, mailbox=mailbox)
    session.select_folder()
    return session
