from __future__ import annotations

import email
import imaplib
from email.message import Message
from typing import List

from mail_fetcher import MailFetcher
from integration import MailSourceRecord
from models import AttachmentMeta, RawEmail
from config import MailboxConfig


class IMAPFetcher(MailFetcher):
    """Thin IMAP adapter.

    Designed so raw mail stays inside the sanitizer boundary. The adapter only
    produces `MailSourceRecord` objects for local downstream sanitization.
    """

    def __init__(self, mailbox: MailboxConfig, *, search_criteria: str = '(UNSEEN)') -> None:
        self.mailbox = mailbox
        self.search_criteria = search_criteria

    def fetch(self) -> List[MailSourceRecord]:
        if not self.mailbox.host or not self.mailbox.username:
            raise ValueError("MailboxConfig.host and username are required for IMAP fetching")

        client = imaplib.IMAP4_SSL(self.mailbox.host, self.mailbox.port or 993) if self.mailbox.use_ssl else imaplib.IMAP4(self.mailbox.host, self.mailbox.port or 143)
        try:
            # Authentication secret intentionally not modeled here; expected to be provided
            # by the integration layer or environment wrapper outside agent-visible code paths.
            raise NotImplementedError("Real credentialed IMAP login should be wired by a local secret-aware runner")
        finally:
            try:
                client.logout()
            except Exception:
                pass


def parse_eml_bytes(source_id: str, payload: bytes) -> MailSourceRecord:
    msg = email.message_from_bytes(payload)
    sender = msg.get("From", "unknown")
    subject = msg.get("Subject", "")
    date = msg.get("Date", "")
    body_text = _extract_text_body(msg)
    snippet = body_text[:200] if body_text else None
    attachments = _extract_attachments(msg)

    return MailSourceRecord(
        source_id=source_id,
        raw_email=RawEmail(
            sender=sender,
            subject=subject,
            date=date,
            body_text=body_text,
            snippet=snippet,
            attachments=attachments,
        ),
    )


def _extract_text_body(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and 'attachment' not in str(part.get('Content-Disposition', '')).lower():
                data = part.get_payload(decode=True) or b''
                charset = part.get_content_charset() or 'utf-8'
                return data.decode(charset, errors='replace')
        return ''
    data = msg.get_payload(decode=True)
    if data is None:
        payload = msg.get_payload()
        return payload if isinstance(payload, str) else ''
    charset = msg.get_content_charset() or 'utf-8'
    return data.decode(charset, errors='replace')


def _extract_attachments(msg: Message) -> list[AttachmentMeta]:
    items: list[AttachmentMeta] = []
    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue
        payload = part.get_payload(decode=True) or b''
        items.append(
            AttachmentMeta(
                filename=filename,
                mime_type=part.get_content_type(),
                size_bytes=len(payload),
            )
        )
    return items
