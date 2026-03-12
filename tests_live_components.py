from __future__ import annotations

from config import MailboxConfig
from imap_client import IMAPSession
from live_fetcher import LiveIMAPFetcher
from secret_binding import bind_mailbox_secret
from secrets_config import MailboxSecrets


class FakeIMAPClient:
    def __init__(self) -> None:
        self.seen_marked: list[bytes] = []

    def select(self, folder):
        return "OK", [b"1"]

    def search(self, charset, criteria):
        return "OK", [b"1 2"]

    def fetch(self, message_id, query):
        payload = (
            b"From: alerts@example.com\n"
            b"Subject: Test message\n"
            b"Date: Thu, 12 Mar 2026 19:00:00 +0000\n"
            b"Content-Type: text/plain; charset=utf-8\n\n"
            b"Hello from email body."
        )
        return "OK", [(b"RFC822", payload)]

    def store(self, message_id, flags_op, flags):
        self.seen_marked.append(message_id)
        return "OK", []

    def logout(self):
        return "BYE", []


def test_live_fetcher_parses_and_marks_seen() -> None:
    mailbox = MailboxConfig(name="test", host="imap.example.com", username="user@example.com")
    session = IMAPSession(client=FakeIMAPClient(), mailbox=mailbox)
    fetcher = LiveIMAPFetcher(session, mark_seen_after_fetch=True)

    records = fetcher.fetch()

    assert len(records) == 2
    assert records[0].raw_email.subject == "Test message"
    assert session.client.seen_marked == [b"1", b"2"]


def test_secret_binding_resolves_env_secret() -> None:
    import os
    os.environ["MAIL_SECRET_TEST"] = "secret-value"
    mailbox = MailboxConfig(name="test", host="imap.example.com", username="user@example.com")
    bound = bind_mailbox_secret(mailbox, MailboxSecrets(password_env="MAIL_SECRET_TEST"))
    assert bound.resolved_secret == "secret-value"
    del os.environ["MAIL_SECRET_TEST"]


def run_tests() -> None:
    tests = [
        test_live_fetcher_parses_and_marks_seen,
        test_secret_binding_resolves_env_secret,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} live component tests passed")


if __name__ == "__main__":
    run_tests()
