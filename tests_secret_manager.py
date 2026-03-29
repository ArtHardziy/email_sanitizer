from __future__ import annotations

import tempfile
from pathlib import Path

from secret_manager import LocalSecretManager


def test_local_secret_manager_put_describe_and_retrieve() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = LocalSecretManager(Path(tmp) / "secrets.json")
        descriptor = manager.put_secret(provider="gmail", secret_type="oauth_refresh_token", secret_value="super-secret")
        assert descriptor.secret_ref_id.startswith("sec_")
        described = manager.describe_secret(descriptor.secret_ref_id)
        assert described.status == "ACTIVE"
        assert not hasattr(described, "value")
        assert manager.get_secret_for_backend(descriptor.secret_ref_id) == "super-secret"


def test_local_secret_manager_put_with_fixed_ref() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = LocalSecretManager(Path(tmp) / "secrets.json")
        descriptor = manager.put_secret_with_ref(
            secret_ref_id="sec_google_oauth_client_secret",
            provider="gmail",
            secret_type="provider_client_secret",
            secret_value="client-secret",
        )
        assert descriptor.secret_ref_id == "sec_google_oauth_client_secret"
        assert manager.get_secret_for_backend("sec_google_oauth_client_secret") == "client-secret"


def test_local_secret_manager_revoke_blocks_future_backend_reads() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = LocalSecretManager(Path(tmp) / "secrets.json")
        descriptor = manager.put_secret(provider="gmail", secret_type="oauth_refresh_token", secret_value="super-secret")
        manager.revoke_secret(descriptor.secret_ref_id)
        try:
            manager.get_secret_for_backend(descriptor.secret_ref_id)
        except ValueError as exc:
            assert "not active" in str(exc)
        else:
            raise AssertionError("Expected revoked secret to be unusable")


def test_local_secret_manager_rotate_supersedes_old_secret() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = LocalSecretManager(Path(tmp) / "secrets.json")
        descriptor = manager.put_secret(provider="gmail", secret_type="oauth_refresh_token", secret_value="super-secret")
        rotated = manager.rotate_secret(descriptor.secret_ref_id, new_secret_value="new-secret")
        old_descriptor = manager.describe_secret(descriptor.secret_ref_id)
        assert old_descriptor.status == "REVOKED"
        assert old_descriptor.superseded_by_secret_ref_id == rotated.secret_ref_id
        assert manager.get_secret_for_backend(rotated.secret_ref_id) == "new-secret"


def run_tests() -> None:
    tests = [
        test_local_secret_manager_put_describe_and_retrieve,
        test_local_secret_manager_put_with_fixed_ref,
        test_local_secret_manager_revoke_blocks_future_backend_reads,
        test_local_secret_manager_rotate_supersedes_old_secret,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} secret manager tests passed")


if __name__ == "__main__":
    run_tests()
