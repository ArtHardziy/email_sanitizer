from __future__ import annotations

import tempfile
from pathlib import Path

from gmail_oauth_backend import GmailOAuthBackend
from oauth_models import OAuthCompleteRequest


def test_gmail_oauth_backend_start_persists_session_and_pkce() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend(Path(tmp) / "oauth_sessions.json")
        session, start = backend.start(user_id="user-1", mailbox_label="Primary Gmail")
        assert session.provider == "gmail"
        assert backend.get_pkce_verifier(session.auth_session_id) is not None
        assert "code_challenge=" in start.authorization_url
        assert backend.store.get(session.auth_session_id) is not None


def test_gmail_oauth_backend_complete_validates_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend(Path(tmp) / "oauth_sessions.json")
        session, _ = backend.start(user_id="user-1")
        result = backend.complete(
            OAuthCompleteRequest(
                provider="gmail",
                auth_session_id=session.auth_session_id,
                authorization_code="code-123",
                state_token=session.state_token,
            ),
            mailbox_id="mbx_123",
        )
        assert result.state == "ACTIVE"


def run_tests() -> None:
    tests = [test_gmail_oauth_backend_start_persists_session_and_pkce, test_gmail_oauth_backend_complete_validates_state]
    for test in tests:
        test()
    print(f"ok: {len(tests)} gmail oauth backend tests passed")


if __name__ == "__main__":
    run_tests()
