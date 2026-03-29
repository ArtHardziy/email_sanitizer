from __future__ import annotations

from pathlib import Path

from oauth_callback_service import OAuthCallbackService
from oauth_models import OAuthCallbackPayload
from secret_manager import LocalSecretManager
from gmail_oauth_backend import GmailOAuthBackend


def _seed_client_secret() -> None:
    manager = LocalSecretManager(Path(".state/email_sanitizer/oauth_secrets.json"))
    try:
        manager.describe_secret("sec_google_oauth_client_secret")
        return
    except ValueError:
        pass
    descriptor = manager.put_secret(
        provider="gmail",
        secret_type="provider_client_secret",
        secret_value="demo-client-secret",
    )
    records = manager._load_all()
    record = records.pop(descriptor.secret_ref_id)
    record.secret_ref_id = "sec_google_oauth_client_secret"
    records[record.secret_ref_id] = record
    manager._save_all(records)


def test_oauth_callback_service_handles_gmail_callback() -> None:
    _seed_client_secret()
    backend = GmailOAuthBackend(Path(".state/email_sanitizer/oauth_sessions.json"), secrets_path=Path(".state/email_sanitizer/oauth_secrets.json"))
    session, _ = backend.start(user_id="user-callback", mailbox_id="mbx_callback", mailbox_label="Callback Gmail")
    service = OAuthCallbackService()
    result = service.handle_callback(
        auth_session_id=session.auth_session_id,
        callback=OAuthCallbackPayload(
            provider="gmail",
            callback_uri="https://backend.example.com/oauth/google/callback",
            state_token=session.state_token,
            authorization_code="code-123",
            scope="https://mail.google.com/ openid email",
        ),
        mailbox_id="mbx_callback",
    )
    assert result.state == "ACTIVE"
    assert result.provider_account_id == "gmail-account-demo"


def run_tests() -> None:
    tests = [test_oauth_callback_service_handles_gmail_callback]
    for test in tests:
        test()
    print(f"ok: {len(tests)} oauth callback service tests passed")


if __name__ == "__main__":
    run_tests()
