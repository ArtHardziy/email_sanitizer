from __future__ import annotations

from aggregate_models import AggregatedMessage
from integration import ProcessedMailRecord


def build_unified_messages(records: list[ProcessedMailRecord]) -> list[AggregatedMessage]:
    items: list[AggregatedMessage] = []
    for record in records:
        mail = record.sanitized
        items.append(
            AggregatedMessage(
                provider="imap",
                mailbox_name=record.source_id.split(":", 2)[1] if ":" in record.source_id else "unknown",
                folder="inbox",
                message_id=record.source_id,
                subject=mail.subject,
                from_address=mail.sender,
                date=mail.date,
                snippet=mail.sanitized_snippet or mail.safe_summary,
                flags={
                    "safe_for_agent": mail.safe_for_agent,
                    "important": any(flag.value in {"medical_content", "financial_content"} for flag in mail.risk_flags),
                },
            )
        )
    return items
