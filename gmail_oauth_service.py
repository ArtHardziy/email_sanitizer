from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from urllib.parse import urlencode

from oauth_models import OAuthCompleteRequest, OAuthCompleteResult, OAuthStartResult
from onboarding_models import MailboxState, OAuthAuthorizationSession
from provider_presets import get_provider_preset


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _future(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def start_google_oauth(*, user_id: str, mailbox_label: str | None = None) -> tuple[OAuthAuthorizationSession, OAuthStartResult]:
    preset = get_provider_preset("gmail")
    assert preset.oauth_config is not None

    state_token = f"st_{uuid4().hex}"
    auth_session = OAuthAuthorizationSession(
        auth_session_id=f"oas_{uuid4().hex[:12]}",
        user_id=user_id,
        provider="gmail",
        mailbox_label=mailbox_label or preset.display_name,
        status="PENDING",
        state_token=state_token,
        redirect_uri=preset.oauth_config.redirect_uri,
        created_at=_now(),
        expires_at=_future(15),
    )

    query = urlencode({
        "client_id": "BACKEND_CONFIGURED_CLIENT_ID",
        "redirect_uri": preset.oauth_config.redirect_uri,
        "response_type": "code",
        "scope": " ".join(preset.oauth_config.scopes),
        "state": state_token,
        "access_type": "offline",
        "prompt": "consent",
    })
    start = OAuthStartResult(
        provider="gmail",
        authorization_url=f"{preset.oauth_config.authorization_url}?{query}",
        state_token=state_token,
        redirect_uri=preset.oauth_config.redirect_uri,
        scopes=preset.oauth_config.scopes,
        pkce_required=preset.oauth_config.use_pkce,
    )
    return auth_session, start


def complete_google_oauth(req: OAuthCompleteRequest, *, mailbox_id: str) -> OAuthCompleteResult:
    return OAuthCompleteResult(
        provider="gmail",
        mailbox_id=mailbox_id,
        credential_type="oauth_refresh_token",
        state=MailboxState.ACTIVE.value,
    )
