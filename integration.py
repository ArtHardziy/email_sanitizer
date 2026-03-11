from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from models import RawEmail, SanitizedEmail, SanitizerPolicy
from sanitizer import sanitize_email


@dataclass(slots=True)
class MailSourceRecord:
    source_id: str
    raw_email: RawEmail


@dataclass(slots=True)
class ProcessedMailRecord:
    source_id: str
    sanitized: SanitizedEmail


def process_mail_records(records: Iterable[MailSourceRecord], policy: SanitizerPolicy | None = None) -> List[ProcessedMailRecord]:
    """Convert raw mail records into agent-safe envelopes.

    This layer is intentionally thin: mail fetching should happen outside,
    and only sanitized envelopes should move downstream to agent-facing flows.
    """
    processed: List[ProcessedMailRecord] = []
    for record in records:
        processed.append(
            ProcessedMailRecord(
                source_id=record.source_id,
                sanitized=sanitize_email(record.raw_email, policy=policy),
            )
        )
    return processed
