from __future__ import annotations

from mailbox_diagnostics import build_mailbox_diagnostic_bundle
from onboarding_models import ConnectedMailbox, CredentialRefStatus, CredentialType, MailboxCredentialRef, MailboxState, OAuthAuthorizationSession, OAuthSessionStatus
from secret_manager import SecretDescriptor


def test_mailbox_diagnostic_bundle_counts_oauth_session_states() -> None:
    mailbox = ConnectedMailbox(
        mailbox_id="mbx_123",
        user_id="user-1",
        provider="gmail",
        display_name="Gmail",
        email_address="user@gmail.com",
        state=MailboxState.ACTIVE,
        auth_mode="oauth",
        created_at="2026-03-13T00:00:00+00:00",
        updated_at="2026-03-13T00:00:00+00:00",
        credential_ref_id="cred_123",
        provider_account_id="gmail-account-demo",
    )
    credential_ref = MailboxCredentialRef(
        credential_ref_id="cred_123",
        mailbox_id="mbx_123",
        provider="gmail",
        credential_type=CredentialType.OAUTH_REFRESH_TOKEN,
        secret_ref_id="sec_123",
        status=CredentialRefStatus.ACTIVE,
        version=1,
        created_at="2026-03-13T00:00:00+00:00",
        updated_at="2026-03-13T00:00:00+00:00",
        auth_mode="oauth",
        provider_account_id="gmail-account-demo",
        client_secret_ref_id="sec_google_oauth_client_secret",
    )
    secret_descriptor = SecretDescriptor(
        secret_ref_id="sec_123",
        provider="gmail",
        secret_type="oauth_refresh_token",
        status="ACTIVE",
        created_at="2026-03-13T00:00:00+00:00",
        updated_at="2026-03-13T00:00:00+00:00",
    )
    sessions = [
        OAuthAuthorizationSession(
            auth_session_id="oas_1", user_id="user-1", provider="gmail", mailbox_label="Gmail", mailbox_id="mbx_123",
            status=OAuthSessionStatus.AUTH_URL_ISSUED, state_token="st1", redirect_uri="https://x", created_at="2026-03-13T00:00:00+00:00", expires_at="2999-01-01T00:00:00+00:00", auth_mode="oauth"
        ),
        OAuthAuthorizationSession(
            auth_session_id="oas_2", user_id="user-1", provider="gmail", mailbox_label="Gmail", mailbox_id="mbx_123",
            status=OAuthSessionStatus.EXPIRED, state_token="st2", redirect_uri="https://x", created_at="2026-03-13T00:00:00+00:00", expires_at="2000-01-01T00:00:00+00:00", auth_mode="oauth"
        ),
    ]
    bundle = build_mailbox_diagnostic_bundle(mailbox, credential_ref, sessions, secret_descriptor)
    assert bundle.provider_account_id == "gmail-account-demo"
    assert bundle.credential_provider_account_id == "gmail-account-demo"
    assert bundle.client_secret_ref_id == "sec_google_oauth_client_secret"
    assert bundle.oauth_session_count == 2
    assert bundle.oauth_pending_count == 1
    assert bundle.oauth_expired_count == 1
    assert bundle.secret_status == "ACTIVE"
    assert isinstance(bundle.remediation_hints, list)


def run_tests() -> None:
    tests = [test_mailbox_diagnostic_bundle_counts_oauth_session_states]
    for test in tests:
        test()
    print(f"ok: {len(tests)} mailbox diagnostics tests passed")


if __name__ == "__main__":
    run_tests()
