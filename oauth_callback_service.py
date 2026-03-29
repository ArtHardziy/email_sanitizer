from __future__ import annotations

from pathlib import Path

from gmail_oauth_backend import GmailOAuthBackend
from oauth_models import OAuthCallbackPayload, OAuthCompleteResult


def _gmail_backend() -> GmailOAuthBackend:
    state_dir = Path(".state/email_sanitizer")
    return GmailOAuthBackend(state_dir / "oauth_sessions.json", secrets_path=state_dir / "oauth_secrets.json")


class OAuthCallbackService:
    def handle_callback(self, *, auth_session_id: str, callback: OAuthCallbackPayload, mailbox_id: str) -> OAuthCompleteResult:
        if callback.provider == "gmail":
            return _gmail_backend().complete_from_callback(auth_session_id, callback, mailbox_id=mailbox_id)
        raise ValueError(f"Unsupported callback provider: {callback.provider}")
