from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json

from onboarding_models import OAuthAuthorizationSession, OAuthSessionStatus


@dataclass(slots=True)
class OAuthSessionDiagnostic:
    auth_session_id: str
    provider: str
    mailbox_id: str | None
    status: str
    expired: bool
    expires_at: str
    failure_reason: str | None
    safe_summary: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_value(raw: OAuthSessionStatus | str) -> str:
    return raw.value if isinstance(raw, OAuthSessionStatus) else str(raw)


def build_oauth_session_diagnostic(session: OAuthAuthorizationSession, *, now_iso: str | None = None) -> OAuthSessionDiagnostic:
    now = now_iso or _now_iso()
    expired = session.expires_at <= now
    status_value = _status_value(session.status)

    if status_value == OAuthSessionStatus.BOUND.value:
        summary = "OAuth session completed and bound to mailbox."
    elif status_value == OAuthSessionStatus.EXPIRED.value or expired:
        summary = "OAuth session expired before completion."
    elif status_value == OAuthSessionStatus.FAILED.value:
        summary = f"OAuth session failed: {session.failure_reason or 'unknown reason'}."
    elif status_value == OAuthSessionStatus.AUTH_URL_ISSUED.value:
        summary = "OAuth consent URL issued; waiting for callback completion."
    elif status_value == OAuthSessionStatus.CALLBACK_RECEIVED.value:
        summary = "OAuth callback received; token exchange pending or in progress."
    elif status_value == OAuthSessionStatus.TOKEN_EXCHANGED.value:
        summary = "OAuth token exchange finished; mailbox binding pending."
    elif status_value == OAuthSessionStatus.REVOKED.value:
        summary = "OAuth session was revoked."
    else:
        summary = "OAuth session is pending."

    return OAuthSessionDiagnostic(
        auth_session_id=session.auth_session_id,
        provider=session.provider,
        mailbox_id=session.mailbox_id,
        status=status_value,
        expired=expired,
        expires_at=session.expires_at,
        failure_reason=session.failure_reason,
        safe_summary=summary,
    )


def diagnostic_to_json(diag: OAuthSessionDiagnostic) -> str:
    return json.dumps(asdict(diag), ensure_ascii=False)
