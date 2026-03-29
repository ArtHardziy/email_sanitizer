from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlencode

from oauth_exchange import GmailLiveTokenExchangeBoundary, GmailTokenExchangeService, TokenExchangeRequest
from oauth_models import OAuthCallbackPayload, OAuthCompleteRequest, OAuthCompleteResult, OAuthStartResult
from oauth_state_store import OAuthSessionStore
from onboarding_models import MailboxState, OAuthAuthorizationSession, OAuthSessionStatus
from pkce_utils import build_pkce_challenge, generate_pkce_verifier
from provider_presets import get_provider_preset
from secret_manager import LocalSecretManager


@dataclass(slots=True)
class StoredOAuthSession:
    session: OAuthAuthorizationSession
    pkce_verifier: str
    pkce_challenge: str


class GmailOAuthBackend:
    def __init__(
        self,
        store_path: str | Path,
        *,
        secrets_path: str | Path | None = None,
        exchange_service: GmailTokenExchangeService | None = None,
    ) -> None:
        self.store = OAuthSessionStore(store_path)
        self.secret_manager = LocalSecretManager(secrets_path or (Path(store_path).parent / "oauth_secrets.json"))
        self.exchange_service = exchange_service or GmailTokenExchangeService()
        self._pkce_cache: dict[str, StoredOAuthSession] = {}

    @classmethod
    def with_live_boundary(cls, store_path: str | Path, *, secrets_path: str | Path | None = None) -> "GmailOAuthBackend":
        return cls(store_path, secrets_path=secrets_path, exchange_service=GmailLiveTokenExchangeBoundary())

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _expire_if_needed(self, session: OAuthAuthorizationSession) -> OAuthAuthorizationSession:
        if session.expires_at <= self._now().isoformat() and session.status not in {OAuthSessionStatus.BOUND, OAuthSessionStatus.EXPIRED, OAuthSessionStatus.REVOKED}:
            session.status = OAuthSessionStatus.EXPIRED
            self.store.update(session)
        return session

    def start(self, *, user_id: str, mailbox_id: str | None = None, mailbox_label: str | None = None) -> tuple[OAuthAuthorizationSession, OAuthStartResult]:
        preset = get_provider_preset("gmail")
        assert preset.oauth_config is not None
        assert preset.oauth_config.client_config is not None

        verifier = generate_pkce_verifier()
        challenge = build_pkce_challenge(verifier)
        state_token = f"st_{uuid4().hex}"
        now = self._now()
        session = OAuthAuthorizationSession(
            auth_session_id=f"oas_{uuid4().hex[:12]}",
            user_id=user_id,
            provider="gmail",
            mailbox_label=mailbox_label or preset.display_name,
            mailbox_id=mailbox_id,
            status=OAuthSessionStatus.AUTH_URL_ISSUED,
            state_token=state_token,
            redirect_uri=preset.oauth_config.redirect_uri,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=15)).isoformat(),
            auth_mode="oauth",
            pkce_required=preset.oauth_config.use_pkce,
            auth_url_issued_at=now.isoformat(),
        )
        self.store.put(session)
        self._pkce_cache[session.auth_session_id] = StoredOAuthSession(session=session, pkce_verifier=verifier, pkce_challenge=challenge)

        query = urlencode({
            "client_id": preset.oauth_config.client_config.client_id,
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
            auth_session_id=session.auth_session_id,
            expires_at=session.expires_at,
            client_id=preset.oauth_config.client_config.client_id,
        )
        return session, start

    def complete(self, req: OAuthCompleteRequest, *, mailbox_id: str) -> OAuthCompleteResult:
        preset = get_provider_preset("gmail")
        assert preset.oauth_config is not None
        assert preset.oauth_config.client_config is not None

        session = self.store.get(req.auth_session_id)
        if not session:
            raise ValueError("OAuth session not found")
        session = self._expire_if_needed(session)
        if session.status == OAuthSessionStatus.EXPIRED:
            raise ValueError("OAuth session expired")
        if session.provider != req.provider:
            raise ValueError("OAuth session provider mismatch")
        if session.mailbox_id and session.mailbox_id != mailbox_id:
            raise ValueError("OAuth session mailbox mismatch")
        if session.state_token != req.state_token:
            session.status = OAuthSessionStatus.FAILED
            session.failure_reason = "state_mismatch"
            self.store.update(session)
            raise ValueError("OAuth state mismatch")
        if req.callback_uri and req.callback_uri != session.redirect_uri:
            session.status = OAuthSessionStatus.FAILED
            session.failure_reason = "callback_uri_mismatch"
            self.store.update(session)
            raise ValueError("OAuth callback URI mismatch")
        if session.status == OAuthSessionStatus.BOUND:
            return OAuthCompleteResult(
                provider="gmail",
                mailbox_id=mailbox_id,
                credential_type="oauth_refresh_token",
                state=MailboxState.ACTIVE.value,
                credential_ref_id=f"cred_reuse_{session.auth_session_id}",
                secret_ref_id=None,
                session_status=session.status.value,
                provider_account_id="gmail-account-demo",
            )
        if session.status not in {OAuthSessionStatus.AUTH_URL_ISSUED, OAuthSessionStatus.CALLBACK_RECEIVED, OAuthSessionStatus.TOKEN_EXCHANGED}:
            raise ValueError("OAuth session is not completable")

        now = self._now().isoformat()
        session.callback_received_at = session.callback_received_at or now
        session.status = OAuthSessionStatus.CALLBACK_RECEIVED
        self.store.update(session)

        stored = self._pkce_cache.get(session.auth_session_id)
        exchange_result = self.exchange_service.exchange_code(TokenExchangeRequest(
            provider="gmail",
            authorization_code=req.authorization_code,
            redirect_uri=session.redirect_uri,
            client_id=preset.oauth_config.client_config.client_id,
            client_secret_ref_id=preset.oauth_config.client_config.client_secret_ref_id,
            code_verifier=stored.pkce_verifier if stored else None,
            callback_uri=req.callback_uri or session.redirect_uri,
            token_endpoint_auth_method=preset.oauth_config.client_config.token_endpoint_auth_method,
        ))
        secret_descriptor = self.secret_manager.put_secret(
            provider="gmail",
            secret_type="oauth_refresh_token",
            secret_value=exchange_result.refresh_token,
        )
        session.status = OAuthSessionStatus.TOKEN_EXCHANGED
        session.token_exchanged_at = now
        self.store.update(session)

        session.status = OAuthSessionStatus.BOUND
        session.mailbox_id = mailbox_id
        session.bound_at = now
        self.store.update(session)
        self._pkce_cache.pop(session.auth_session_id, None)

        return OAuthCompleteResult(
            provider="gmail",
            mailbox_id=mailbox_id,
            credential_type="oauth_refresh_token",
            state=MailboxState.ACTIVE.value,
            credential_ref_id=f"cred_{session.auth_session_id}",
            secret_ref_id=secret_descriptor.secret_ref_id,
            session_status=session.status.value,
            provider_account_id=exchange_result.provider_account_id,
        )

    def complete_from_callback(self, auth_session_id: str, callback: OAuthCallbackPayload, *, mailbox_id: str) -> OAuthCompleteResult:
        if callback.error:
            session = self.store.get(auth_session_id)
            if session:
                session.status = OAuthSessionStatus.FAILED
                session.failure_reason = callback.error
                self.store.update(session)
            raise ValueError(f"OAuth callback error: {callback.error}")
        return self.complete(
            OAuthCompleteRequest(
                provider=callback.provider,
                auth_session_id=auth_session_id,
                authorization_code=callback.authorization_code,
                state_token=callback.state_token,
                callback_uri=callback.callback_uri,
            ),
            mailbox_id=mailbox_id,
        )

    def get_pkce_verifier(self, auth_session_id: str) -> str | None:
        stored = self._pkce_cache.get(auth_session_id)
        return stored.pkce_verifier if stored else None

    def get_session(self, auth_session_id: str) -> OAuthAuthorizationSession | None:
        session = self.store.get(auth_session_id)
        if not session:
            return None
        return self._expire_if_needed(session)

    def list_sessions(self) -> list[OAuthAuthorizationSession]:
        sessions = self.store.list_all()
        return [self._expire_if_needed(session) for session in sessions]

    def cleanup_expired_sessions(self) -> list[str]:
        removed: list[str] = []
        now_iso = self._now().isoformat()
        for session in self.store.list_expired(now_iso=now_iso):
            if session.status != OAuthSessionStatus.BOUND:
                session.status = OAuthSessionStatus.EXPIRED
                self.store.update(session)
                self._pkce_cache.pop(session.auth_session_id, None)
                removed.append(session.auth_session_id)
        return removed
