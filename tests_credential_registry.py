from __future__ import annotations

import tempfile
from pathlib import Path

from credential_registry import CredentialRegistry
from onboarding_models import CredentialRefStatus, CredentialType, MailboxCredentialRef


def test_credential_registry_put_get_and_list_for_mailbox() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = CredentialRegistry(Path(tmp) / "credential_refs.json")
        ref = MailboxCredentialRef(
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
        )
        registry.put(ref)
        loaded = registry.get("cred_123")
        assert loaded is not None
        assert loaded.mailbox_id == "mbx_123"
        listed = registry.list_for_mailbox("mbx_123")
        assert len(listed) == 1
        assert listed[0].credential_ref_id == "cred_123"


def run_tests() -> None:
    tests = [test_credential_registry_put_get_and_list_for_mailbox]
    for test in tests:
        test()
    print(f"ok: {len(tests)} credential registry tests passed")


if __name__ == "__main__":
    run_tests()
