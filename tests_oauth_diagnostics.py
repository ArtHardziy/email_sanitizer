from __future__ import annotations

from oauth_diagnostics import build_oauth_session_diagnostic
from onboarding_models import OAuthAuthorizationSession, OAuthSessionStatus


def test_oauth_diagnostic_marks_expired_and_summarizes() -> None:
    session = OAuthAuthorizationSession(
        auth_session_id="oas_123",
        user_id="user-1",
        provider="gmail",
        mailbox_label="Gmail",
        mailbox_id="mbx_123",
        status=OAuthSessionStatus.AUTH_URL_ISSUED,
        state_token="st_123",
        redirect_uri="https://example.com/callback",
        created_at="2026-03-13T00:00:00+00:00",
        expires_at="2000-01-01T00:00:00+00:00",
        auth_mode="oauth",
    )
    diag = build_oauth_session_diagnostic(session, now_iso="2026-03-13T01:00:00+00:00")
    assert diag.expired is True
    assert "expired" in diag.safe_summary.lower()


def run_tests() -> None:
    tests = [test_oauth_diagnostic_marks_expired_and_summarizes]
    for test in tests:
        test()
    print(f"ok: {len(tests)} oauth diagnostics tests passed")


if __name__ == "__main__":
    run_tests()
