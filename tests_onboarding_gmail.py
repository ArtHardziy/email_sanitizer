from __future__ import annotations

from pathlib import Path

from onboarding_service import complete_auth, connect_mailbox
from secret_manager import LocalSecretManager


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


def test_connect_mailbox_gmail_includes_google_auth_url() -> None:
    _seed_client_secret()
    result = connect_mailbox(user_id="user-1", provider="gmail", email_address="user@gmail.com")
    assert result.auth_session is not None
    assert result.auth_session.provider == "gmail"
    assert result.instructions[0].step == "oauth_client"
    assert "client metadata" in result.instructions[0].details.lower()
    assert result.instructions[1].step == "oauth_client_runtime"
    assert "secret ref" in result.instructions[1].details.lower()
    assert result.instructions[2].step == "oauth_start"
    assert "accounts.google.com" in result.instructions[2].details


def test_complete_auth_gmail_binds_credential_ref() -> None:
    _seed_client_secret()
    connected = connect_mailbox(user_id="user-1", provider="gmail", email_address="user@gmail.com")
    assert connected.auth_session is not None
    completed = complete_auth(
        mailbox=connected.mailbox,
        provider="gmail",
        auth_session_id=connected.auth_session.auth_session_id,
        state_token=connected.auth_session.state_token,
        authorization_code="code-123",
    )
    assert completed.mailbox.state.value == "ACTIVE"
    assert completed.mailbox.provider_account_id == "gmail-account-demo"
    assert completed.credential_ref is not None
    assert completed.credential_ref.secret_ref_id is not None
    assert completed.credential_ref.provider == "gmail"
    assert completed.credential_ref.provider_account_id == "gmail-account-demo"
    assert completed.credential_ref.client_secret_ref_id == "sec_google_oauth_client_secret"


def run_tests() -> None:
    tests = [
        test_connect_mailbox_gmail_includes_google_auth_url,
        test_complete_auth_gmail_binds_credential_ref,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} onboarding gmail tests passed")


if __name__ == "__main__":
    run_tests()
