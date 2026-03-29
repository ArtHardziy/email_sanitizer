from __future__ import annotations

from mailbox_status import build_mailbox_health, render_mailbox_status
from onboarding_models import ConnectedMailbox, CredentialRefStatus, CredentialType, MailboxCredentialRef, MailboxState
from secret_manager import SecretDescriptor


def _mailbox() -> ConnectedMailbox:
    return ConnectedMailbox(
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


def _credential_ref() -> MailboxCredentialRef:
    return MailboxCredentialRef(
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
        last_validated_at="2026-03-13T00:00:00+00:00",
    )


def _secret_descriptor(status: str = "ACTIVE") -> SecretDescriptor:
    return SecretDescriptor(
        secret_ref_id="sec_123",
        provider="gmail",
        secret_type="oauth_refresh_token",
        status=status,
        created_at="2026-03-13T00:00:00+00:00",
        updated_at="2026-03-13T00:00:00+00:00",
    )


def test_build_mailbox_health_marks_active_mailbox_healthy() -> None:
    health = build_mailbox_health(_mailbox(), _credential_ref(), _secret_descriptor())
    assert health.health_status == "healthy"


def test_build_mailbox_health_marks_missing_credential_ref_degraded() -> None:
    health = build_mailbox_health(_mailbox(), None)
    assert health.health_status == "degraded"
    assert health.last_error_code == "missing_credential_ref"


def test_build_mailbox_health_marks_missing_secret_descriptor_degraded() -> None:
    health = build_mailbox_health(_mailbox(), _credential_ref(), None)
    assert health.health_status == "degraded"
    assert health.last_error_code == "secret_ref_missing"


def test_render_mailbox_status_contains_provider_metadata_health_ref_secret_and_hints() -> None:
    status = render_mailbox_status(_mailbox(), _credential_ref(), _secret_descriptor())
    assert status["mailbox"]["mailbox_id"] == "mbx_123"
    assert status["provider_account_id"] == "gmail-account-demo"
    assert status["credential_provider_account_id"] == "gmail-account-demo"
    assert status["client_secret_ref_id"] == "sec_google_oauth_client_secret"
    assert status["credential_ref"]["credential_ref_id"] == "cred_123"
    assert status["secret_descriptor"]["secret_ref_id"] == "sec_123"
    assert status["health"]["health_status"] == "healthy"
    assert isinstance(status["remediation_hints"], list)


def run_tests() -> None:
    tests = [
        test_build_mailbox_health_marks_active_mailbox_healthy,
        test_build_mailbox_health_marks_missing_credential_ref_degraded,
        test_build_mailbox_health_marks_missing_secret_descriptor_degraded,
        test_render_mailbox_status_contains_provider_metadata_health_ref_secret_and_hints,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} mailbox status tests passed")


if __name__ == "__main__":
    run_tests()
