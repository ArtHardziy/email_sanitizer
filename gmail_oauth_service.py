from __future__ import annotations

from pathlib import Path

from gmail_oauth_backend import GmailOAuthBackend
from oauth_models import OAuthCompleteRequest, OAuthCompleteResult, OAuthStartResult
from onboarding_models import OAuthAuthorizationSession


def _backend() -> GmailOAuthBackend:
    state_dir = Path(".state/email_sanitizer")
    return GmailOAuthBackend(state_dir / "oauth_sessions.json", secrets_path=state_dir / "oauth_secrets.json")


def start_google_oauth(*, user_id: str, mailbox_label: str | None = None) -> tuple[OAuthAuthorizationSession, OAuthStartResult]:
    return _backend().start(user_id=user_id, mailbox_label=mailbox_label)


def complete_google_oauth(req: OAuthCompleteRequest, *, mailbox_id: str) -> OAuthCompleteResult:
    return _backend().complete(req, mailbox_id=mailbox_id)
