from __future__ import annotations

import tempfile
from pathlib import Path

from mailbox_registry import MailboxRegistry
from onboarding_models import ConnectedMailbox, MailboxState


def test_mailbox_registry_put_get_and_list_for_user() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = MailboxRegistry(Path(tmp) / "mailboxes.json")
        mailbox = ConnectedMailbox(
            mailbox_id="mbx_123",
            user_id="user-1",
            provider="gmail",
            display_name="Gmail",
            email_address="user@gmail.com",
            state=MailboxState.PENDING_AUTH,
            auth_mode="oauth",
            created_at="2026-03-13T00:00:00+00:00",
            updated_at="2026-03-13T00:00:00+00:00",
        )
        registry.put(mailbox)
        loaded = registry.get("mbx_123")
        assert loaded is not None
        assert loaded.provider == "gmail"
        listed = registry.list_for_user("user-1")
        assert len(listed) == 1
        assert listed[0].mailbox_id == "mbx_123"


def run_tests() -> None:
    tests = [test_mailbox_registry_put_get_and_list_for_user]
    for test in tests:
        test()
    print(f"ok: {len(tests)} mailbox registry tests passed")


if __name__ == "__main__":
    run_tests()
