from __future__ import annotations

from onboarding_service import connect_mailbox


def test_connect_mailbox_gmail_includes_google_auth_url() -> None:
    result = connect_mailbox(user_id="user-1", provider="gmail", email_address="user@gmail.com")
    assert result.auth_session is not None
    assert result.auth_session.provider == "gmail"
    assert result.instructions[0].step == "oauth_start"
    assert "accounts.google.com" in result.instructions[0].details


def run_tests() -> None:
    tests = [test_connect_mailbox_gmail_includes_google_auth_url]
    for test in tests:
        test()
    print(f"ok: {len(tests)} onboarding gmail tests passed")


if __name__ == "__main__":
    run_tests()
