from __future__ import annotations

import tempfile
from pathlib import Path

from client_secret_registry import validate_provider_client_secret_ref, validate_provider_client_secret_runtime
from secret_manager import LocalSecretManager


def test_client_secret_metadata_validation_for_gmail() -> None:
    result = validate_provider_client_secret_ref("gmail")
    assert result.ok is True
    assert result.client_id == "BACKEND_CONFIGURED_CLIENT_ID"
    assert result.client_secret_ref_id == "sec_google_oauth_client_secret"


def test_client_secret_runtime_validation_detects_missing_secret() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_provider_client_secret_runtime("gmail", secrets_path=Path(tmp) / "oauth_secrets.json")
        assert result.ok is False
        assert "missing in secret storage" in result.safe_message


def test_client_secret_runtime_validation_accepts_active_secret() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = LocalSecretManager(Path(tmp) / "oauth_secrets.json")
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
        result = validate_provider_client_secret_runtime("gmail", secrets_path=Path(tmp) / "oauth_secrets.json")
        assert result.ok is True
        assert result.client_secret_ref_id == "sec_google_oauth_client_secret"


def run_tests() -> None:
    tests = [
        test_client_secret_metadata_validation_for_gmail,
        test_client_secret_runtime_validation_detects_missing_secret,
        test_client_secret_runtime_validation_accepts_active_secret,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} client secret registry tests passed")


if __name__ == "__main__":
    run_tests()
