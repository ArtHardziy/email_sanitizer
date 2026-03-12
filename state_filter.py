from __future__ import annotations

from integration import MailSourceRecord
from state_store import MailState


def filter_unprocessed(records: list[MailSourceRecord], state: MailState) -> list[MailSourceRecord]:
    return [record for record in records if record.source_id not in state.processed_ids]


def processed_ids(records: list[MailSourceRecord]) -> list[str]:
    return [record.source_id for record in records]
