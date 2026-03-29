from __future__ import annotations

from config import MailboxConfig
from diagnostics import diagnose_combined, diagnose_runtime
from runtime_config import build_runtime
from validation import validate_mailbox_config


def test_validate_mailbox_config_flags_missing_host() -> None:
    mailbox = MailboxConfig(name="personal", host=None, username="user@example.com")
    report = validate_mailbox_config(mailbox)
    assert report.ok is False
    assert any(issue.field == "host" for issue in report.issues)


def test_diagnose_runtime_reports_secret_absent() -> None:
    mailbox = MailboxConfig(name="personal", host="imap.example.com", username="user@example.com")
    runtime = build_runtime(mailbox)
    diag = diagnose_runtime(runtime)
    assert diag.config_ok is True
    assert diag.secret_resolved is False


def test_diagnose_combined_returns_runtime_and_onboarding_sections() -> None:
    mailbox = MailboxConfig(name="personal", host="imap.example.com", username="user@example.com")
    runtime = build_runtime(mailbox)
    diag = diagnose_combined(runtime)
    assert diag.runtime.mailbox_name == "personal"
    assert isinstance(diag.onboarding, list)
    if diag.onboarding:
        assert hasattr(diag.onboarding[0], "remediation_hints")
        assert hasattr(diag.onboarding[0], "provider_account_id")
        assert hasattr(diag.onboarding[0], "client_secret_ref_id")


def run_tests() -> None:
    tests = [
        test_validate_mailbox_config_flags_missing_host,
        test_diagnose_runtime_reports_secret_absent,
        test_diagnose_combined_returns_runtime_and_onboarding_sections,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} validation/diagnostic tests passed")


if __name__ == "__main__":
    run_tests()
