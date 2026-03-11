from models import AllowedView, RawEmail, RiskFlag
from summary_builder import build_content_aware_summary


def test_summary_ignores_footer_noise() -> None:
    email = RawEmail(
        sender="alerts@example.com",
        subject="Status update",
        date="2026-03-11T16:00:00Z",
        body_text="Important service update. View in browser. Unsubscribe here.",
    )
    summary = build_content_aware_summary(email, [], AllowedView.ALLOW_SANITIZED, email.body_text)

    assert "Important service update" in summary
    assert "Unsubscribe" not in summary


def test_summary_for_restricted_content_mentions_flags() -> None:
    email = RawEmail(
        sender="alerts@example.com",
        subject="Security notice",
        date="2026-03-11T16:00:00Z",
        body_text="Please confirm your identity.",
    )
    summary = build_content_aware_summary(email, [RiskFlag.CREDENTIAL_REQUEST], AllowedView.SUMMARY_ONLY, email.body_text)

    assert "credential_request" in summary


def run_tests() -> None:
    tests = [
        test_summary_ignores_footer_noise,
        test_summary_for_restricted_content_mentions_flags,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} summary tests passed")


if __name__ == "__main__":
    run_tests()
