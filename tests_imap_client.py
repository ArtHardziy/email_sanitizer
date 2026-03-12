from __future__ import annotations

from config import MailboxConfig
from imap_client import IMAPSession


class FakeClient:
    def __init__(self):
        self.selected = None
        self.stored = []

    def select(self, folder):
        self.selected = folder
        return "OK", [b"1"]

    def search(self, charset, criteria):
        return "OK", [b"10 11"]

    def fetch(self, message_id, query):
        return "OK", [(b"RFC822", b"hello")]

    def store(self, message_id, op, flags):
        self.stored.append((message_id, op, flags))
        return "OK", []

    def logout(self):
        return "BYE", []


def test_imap_session_search_fetch_and_mark_seen() -> None:
    mailbox = MailboxConfig(name="test", host="imap.example.com", username="user@example.com")
    session = IMAPSession(client=FakeClient(), mailbox=mailbox)
    session.select_folder()
    ids = session.search_unseen()
    payload = session.fetch_rfc822(ids[0])
    session.mark_seen(ids)

    assert ids == [b"10", b"11"]
    assert payload == b"hello"
    assert len(session.client.stored) == 2


def run_tests() -> None:
    tests = [test_imap_session_search_fetch_and_mark_seen]
    for test in tests:
        test()
    print(f"ok: {len(tests)} imap client tests passed")


if __name__ == "__main__":
    run_tests()
