from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from mailbox_status import build_mailbox_health, remediation_hints_for_error
from onboarding_models import ConnectedMailbox, MailboxCredentialRef, OAuthAuthorizationSession
from oauth_diagnostics import build_oauth_session_diagnostic
from secret_manager import SecretDescriptor


@dataclass(slots=True)
class MailboxDiagnosticBundle:
    mailbox_id: str
    provider: str
    mailbox_state: str
    provider_account_id: str | None
    credential_ref_id: str | None
    credential_provider_account_id: str | None
    client_secret_ref_id: str | None
    secret_ref_id: str | None
    secret_status: str | None
    health_status: str
    health_error_code: str | None
    remediation_hints: list[str]
    oauth_session_count: int
    oauth_pending_count: int
    oauth_expired_count: int
    oauth_failed_count: int
    oauth_sessions: list[dict[str, object]]


def build_mailbox_diagnostic_bundle(
    mailbox: ConnectedMailbox,
    credential_ref: MailboxCredentialRef | None = None,
    oauth_sessions: list[OAuthAuthorizationSession] | None = None,
    secret_descriptor: SecretDescriptor | None = None,
) -> MailboxDiagnosticBundle:
    health = build_mailbox_health(mailbox, credential_ref, secret_descriptor)
    session_diags = [asdict(build_oauth_session_diagnostic(session)) for session in (oauth_sessions or [])]
    pending = sum(1 for item in session_diags if item["status"] in {"AUTH_URL_ISSUED", "CALLBACK_RECEIVED", "TOKEN_EXCHANGED", "CREATED"})
    expired = sum(1 for item in session_diags if item["status"] == "EXPIRED")
    failed = sum(1 for item in session_diags if item["status"] == "FAILED")
    return MailboxDiagnosticBundle(
        mailbox_id=mailbox.mailbox_id,
        provider=mailbox.provider,
        mailbox_state=mailbox.state.value,
        provider_account_id=mailbox.provider_account_id,
        credential_ref_id=credential_ref.credential_ref_id if credential_ref else None,
        credential_provider_account_id=credential_ref.provider_account_id if credential_ref else None,
        client_secret_ref_id=credential_ref.client_secret_ref_id if credential_ref else None,
        secret_ref_id=credential_ref.secret_ref_id if credential_ref else None,
        secret_status=secret_descriptor.status if secret_descriptor else None,
        health_status=health.health_status,
        health_error_code=health.last_error_code,
        remediation_hints=remediation_hints_for_error(health.last_error_code),
        oauth_session_count=len(session_diags),
        oauth_pending_count=pending,
        oauth_expired_count=expired,
        oauth_failed_count=failed,
        oauth_sessions=session_diags,
    )


def bundle_to_json(bundle: MailboxDiagnosticBundle) -> str:
    return json.dumps(asdict(bundle), ensure_ascii=False)
