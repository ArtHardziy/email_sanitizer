from __future__ import annotations

import tempfile
from pathlib import Path

from client_secret_registry import validate_provider_client_secret_ref
from gmail_oauth_backend import GmailOAuthBackend
from oauth_models import OAuthCallbackPayload, OAuthCompleteRequest
from provider_presets import get_provider_preset


def test_gmail_oauth_backend_start_persists_session_and_pkce() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend(Path(tmp) / "oauth_sessions.json")
        session, start = backend.start(user_id="user-1", mailbox_id="mbx_123", mailbox_label="Primary Gmail")
        assert session.provider == "gmail"
        assert session.mailbox_id == "mbx_123"
        assert backend.get_pkce_verifier(session.auth_session_id) is not None
        assert start.client_id == "BACKEND_CONFIGURED_CLIENT_ID"
        assert "code_challenge=" in start.authorization_url
        assert start.auth_session_id == session.auth_session_id
        assert backend.store.get(session.auth_session_id) is not None


def test_gmail_client_secret_validation_uses_provider_metadata() -> None:
    preset = get_provider_preset("gmail")
    assert preset.oauth_config is not None
    assert preset.oauth_config.client_config is not None
    validation = validate_provider_client_secret_ref("gmail")
    assert validation.ok is True
    assert validation.client_secret_ref_id == "sec_google_oauth_client_secret"


def test_gmail_oauth_backend_complete_validates_state_and_binds_secret_ref() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend(Path(tmp) / "oauth_sessions.json")
        session, _ = backend.start(user_id="user-1", mailbox_id="mbx_123")
        result = backend.complete(
            OAuthCompleteRequest(
                provider="gmail",
                auth_session_id=session.auth_session_id,
                authorization_code="code-123",
                state_token=session.state_token,
                callback_uri="https://backend.example.com/oauth/google/callback",
            ),
            mailbox_id="mbx_123",
        )
        assert result.state == "ACTIVE"
        assert result.secret_ref_id is not None
        assert result.provider_account_id == "gmail-account-demo"
        assert result.session_status == "BOUND"
        assert backend.secret_manager.describe_secret(result.secret_ref_id).status == "ACTIVE"


def test_gmail_oauth_backend_complete_from_callback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend(Path(tmp) / "oauth_sessions.json")
        session, _ = backend.start(user_id="user-1", mailbox_id="mbx_123")
        result = backend.complete_from_callback(
            session.auth_session_id,
            OAuthCallbackPayload(
                provider="gmail",
                callback_uri="https://backend.example.com/oauth/google/callback",
                state_token=session.state_token,
                authorization_code="code-123",
                scope="https://mail.google.com/ openid email",
            ),
            mailbox_id="mbx_123",
        )
        assert result.provider_account_id == "gmail-account-demo"
        assert result.state == "ACTIVE"


def test_gmail_oauth_backend_live_boundary_factory() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend.with_live_boundary(Path(tmp) / "oauth_sessions.json")
        session, _ = backend.start(user_id="user-1", mailbox_id="mbx_123")
        result = backend.complete(
            OAuthCompleteRequest(
                provider="gmail",
                auth_session_id=session.auth_session_id,
                authorization_code="code-123",
                state_token=session.state_token,
                callback_uri="https://backend.example.com/oauth/google/callback",
            ),
            mailbox_id="mbx_123",
        )
        assert result.provider_account_id == "gmail-live-boundary-account"


def test_gmail_oauth_backend_rejects_expired_session() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend(Path(tmp) / "oauth_sessions.json")
        session, _ = backend.start(user_id="user-1", mailbox_id="mbx_123")
        stored = backend.store.get(session.auth_session_id)
        assert stored is not None
        stored.expires_at = "2000-01-01T00:00:00+00:00"
        backend.store.update(stored)
        try:
            backend.complete(
                OAuthCompleteRequest(
                    provider="gmail",
                    auth_session_id=session.auth_session_id,
                    authorization_code="code-123",
                    state_token=session.state_token,
                    callback_uri="https://backend.example.com/oauth/google/callback",
                ),
                mailbox_id="mbx_123",
            )
        except ValueError as exc:
            assert "expired" in str(exc)
        else:
            raise AssertionError("Expected expired session failure")


def test_gmail_oauth_backend_rejects_callback_uri_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend(Path(tmp) / "oauth_sessions.json")
        session, _ = backend.start(user_id="user-1", mailbox_id="mbx_123")
        try:
            backend.complete(
                OAuthCompleteRequest(
                    provider="gmail",
                    auth_session_id=session.auth_session_id,
                    authorization_code="code-123",
                    state_token=session.state_token,
                    callback_uri="https://evil.example.com/callback",
                ),
                mailbox_id="mbx_123",
            )
        except ValueError as exc:
            assert "callback URI mismatch" in str(exc)
        else:
            raise AssertionError("Expected callback URI mismatch failure")


def test_gmail_oauth_backend_cleanup_marks_expired_sessions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = GmailOAuthBackend(Path(tmp) / "oauth_sessions.json")
        session, _ = backend.start(user_id="user-1", mailbox_id="mbx_123")
        stored = backend.store.get(session.auth_session_id)
        assert stored is not None
        stored.expires_at = "2000-01-01T00:00:00+00:00"
        backend.store.update(stored)
        cleaned = backend.cleanup_expired_sessions()
        assert session.auth_session_id in cleaned
        updated = backend.get_session(session.auth_session_id)
        assert updated is not None
        assert updated.status.value == "EXPIRED"


def run_tests() -> None:
    tests = [
        test_gmail_oauth_backend_start_persists_session_and_pkce,
        test_gmail_client_secret_validation_uses_provider_metadata,
        test_gmail_oauth_backend_complete_validates_state_and_binds_secret_ref,
        test_gmail_oauth_backend_complete_from_callback,
        test_gmail_oauth_backend_live_boundary_factory,
        test_gmail_oauth_backend_rejects_expired_session,
        test_gmail_oauth_backend_rejects_callback_uri_mismatch,
        test_gmail_oauth_backend_cleanup_marks_expired_sessions,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} gmail oauth backend tests passed")


if __name__ == "__main__":
    run_tests()
