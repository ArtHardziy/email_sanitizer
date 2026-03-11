from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol

from integration import MailSourceRecord
from models import AttachmentMeta, RawEmail


class MailFetcher(Protocol):
    def fetch(self) -> List[MailSourceRecord]: ...


@dataclass(slots=True)
class StaticMailFetcher:
    """Development fetcher for local testing.

    Real IMAP/Gmail integrations should implement the same `fetch()` contract
    and keep raw messages inside the sanitizer boundary.
    """

    records: list[MailSourceRecord]

    def fetch(self) -> List[MailSourceRecord]:
        return list(self.records)


def build_record(
    *,
    source_id: str,
    sender: str,
    subject: str,
    date: str,
    body_text: str,
    snippet: str | None = None,
    attachments: list[AttachmentMeta] | None = None,
) -> MailSourceRecord:
    return MailSourceRecord(
        source_id=source_id,
        raw_email=RawEmail(
            sender=sender,
            subject=subject,
            date=date,
            body_text=body_text,
            snippet=snippet,
            attachments=attachments or [],
        ),
    )
