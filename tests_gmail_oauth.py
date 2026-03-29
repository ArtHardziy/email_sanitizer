from __future__ import annotations

from gmail_oauth_service import complete_google_oauth, start_google_oauth
from oauth_models import OAuthCompleteRequest


def test_start_google_oauth_returns_session_and_url() -> None:
    session, start = start_google_oauth(user_id="user-1", mailbox_label="Primary Gmail")
    assert session.provider == "gmail"
    assert start.provider == "gmail"
    assert start.auth_session_id == session.auth_session_id
    assert start.client_id == "BACKEND_CONFIGURED_CLIENT_ID"
    assert "accounts.google.com" in start.authorization_url
    assert start.pkce_required is True
    assert any("mail.google.com" in scope for scope in start.scopes)


def test_complete_google_oauth_returns_active_result() -> None:
    session, _ = start_google_oauth(user_id="user-1", mailbox_label="Primary Gmail")
    result = complete_google_oauth(
        OAuthCompleteRequest(
            provider="gmail",
            auth_session_id=session.auth_session_id,
            authorization_code="code-123",
            state_token=session.state_token,
            callback_uri="https://backend.example.com/oauth/google/callback",
        ),
        mailbox_id="mbx_123",
    )
    assert result.provider == "gmail"
    assert result.mailbox_id == "mbx_123"
    assert result.state == "ACTIVE"
    assert result.secret_ref_id is not None
    assert result.provider_account_id == "gmail-account-demo"


def run_tests() -> None:
    tests = [test_start_google_oauth_returns_session_and_url, test_complete_google_oauth_returns_active_result]
    for test in tests:
        test()
    print(f"ok: {len(tests)} gmail oauth tests passed")


if __name__ == "__main__":
    run_tests()
