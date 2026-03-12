from __future__ import annotations

from dataclasses import dataclass, field

from imap_adapter import parse_eml_bytes
from imap_client import IMAPSession
from integration import MailSourceRecord
from mail_fetcher import MailFetcher


@dataclass(slots=True)
class LiveIMAPFetcher(MailFetcher):
    session: IMAPSession
    mark_seen_after_fetch: bool = False
    last_fetched_ids: list[bytes] = field(default_factory=list)

    def fetch(self) -> list[MailSourceRecord]:
        message_ids = self.session.search_unseen()
        records: list[MailSourceRecord] = []
        for message_id in message_ids:
            payload = self.session.fetch_rfc822(message_id)
            record = parse_eml_bytes(f"imap:{self.session.mailbox.name}:{message_id.decode()}", payload)
            records.append(record)
        self.last_fetched_ids = list(message_ids)
        if self.mark_seen_after_fetch and message_ids:
            self.session.mark_seen(message_ids)
        return records
