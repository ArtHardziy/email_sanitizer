from __future__ import annotations

from onboarding_models import MailboxState
from onboarding_service import complete_auth, connect_mailbox, disconnect_mailbox, reauth_mailbox


def test_connect_mailbox_gmail_starts_pending_auth() -> None:
    result = connect_mailbox(user_id="user-1", provider="gmail", email_address="user@gmail.com")
    assert result.mailbox.state == MailboxState.PENDING_AUTH
    assert result.auth_session is not None
    assert result.mailbox.provider == "gmail"


def test_complete_auth_activates_mailbox() -> None:
    connected = connect_mailbox(user_id="user-1", provider="icloud", email_address="user@icloud.com")
    result = complete_auth(mailbox=connected.mailbox, provider="icloud")
    assert result.mailbox.state == MailboxState.ACTIVE
    assert result.credential_ref is not None


def test_reauth_and_disconnect_transitions() -> None:
    connected = connect_mailbox(user_id="user-1", provider="yandex", email_address="user@yandex.ru")
    mailbox = reauth_mailbox(connected.mailbox)
    assert mailbox.state == MailboxState.REAUTH_REQUIRED
    disconnected = disconnect_mailbox(mailbox)
    assert disconnected.mailbox.state == MailboxState.DISCONNECTED


def run_tests() -> None:
    tests = [
        test_connect_mailbox_gmail_starts_pending_auth,
        test_complete_auth_activates_mailbox,
        test_reauth_and_disconnect_transitions,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} onboarding tests passed")


if __name__ == "__main__":
    run_tests()
