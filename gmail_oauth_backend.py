from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4
from urllib.parse import urlencode

from onboarding_models import MailboxState, OAuthAuthorizationSession
from oauth_models import OAuthCompleteRequest, OAuthCompleteResult, OAuthStartResult
from oauth_state_store import OAuthSessionStore
from pkce_utils import build_pkce_challenge, generate_pkce_verifier
from provider_presets import get_provider_preset


@dataclass(slots=True)
class StoredOAuthSession:
    session: OAuthAuthorizationSession
    pkce_verifier: str
    pkce_challenge: str


class GmailOAuthBackend:
    def __init__(self, store_path: str | Path) -> None:
        self.store = OAuthSessionStore(store_path)
        self._pkce_cache: dict[str, StoredOAuthSession] = {}

    def start(self, *, user_id: str, mailbox_label: str | None = None) -> tuple[OAuthAuthorizationSession, OAuthStartResult]:
        preset = get_provider_preset("gmail")
        assert preset.oauth_config is not None

        verifier = generate_pkce_verifier()
        challenge = build_pkce_challenge(verifier)
        state_token = f"st_{uuid4().hex}"
        now = datetime.now(timezone.utc)
        session = OAuthAuthorizationSession(
            auth_session_id=f"oas_{uuid4().hex[:12]}",
            user_id=user_id,
            provider="gmail",
            mailbox_label=mailbox_label or preset.display_name,
            status="PENDING",
            state_token=state_token,
            redirect_uri=preset.oauth_config.redirect_uri,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=15)).isoformat(),
        )
        self.store.put(session)
        self._pkce_cache[session.auth_session_id] = StoredOAuthSession(session=session, pkce_verifier=verifier, pkce_challenge=challenge)

        query = urlencode({
            "client_id": "BACKEND_CONFIGURED_CLIENT_ID",
            "redirect_uri": preset.oauth_config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(preset.oauth_config.scopes),
            "state": state_token,
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })
        start = OAuthStartResult(
            provider="gmail",
            authorization_url=f"{preset.oauth_config.authorization_url}?{query}",
            state_token=state_token,
            redirect_uri=preset.oauth_config.redirect_uri,
            scopes=preset.oauth_config.scopes,
            pkce_required=preset.oauth_config.use_pkce,
        )
        return session, start

    def complete(self, req: OAuthCompleteRequest, *, mailbox_id: str) -> OAuthCompleteResult:
        session = self.store.get(req.auth_session_id)
        if not session:
            raise ValueError("OAuth session not found")
        if session.provider != "gmail":
            raise ValueError("OAuth session provider mismatch")
        if session.state_token != req.state_token:
            raise ValueError("OAuth state mismatch")
        session.status = "COMPLETED"
        self.store.update(session)
        return OAuthCompleteResult(
            provider="gmail",
            mailbox_id=mailbox_id,
            credential_type="oauth_refresh_token",
            state=MailboxState.ACTIVE.value,
        )

    def get_pkce_verifier(self, auth_session_id: str) -> str | None:
        stored = self._pkce_cache.get(auth_session_id)
        return stored.pkce_verifier if stored else None
