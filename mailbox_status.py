from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json

from onboarding_models import ConnectedMailbox, CredentialRefStatus, MailboxConnectionHealth, MailboxCredentialRef, MailboxState
from secret_manager import SecretDescriptor


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def remediation_hints_for_error(error_code: str | None) -> list[str]:
    if error_code == "auth_incomplete":
        return [
            "Finish the provider auth flow for this mailbox.",
            "If the auth session expired, start a fresh connect flow.",
        ]
    if error_code == "missing_credential_ref":
        return [
            "Re-run auth completion to bind a credential ref to the mailbox.",
            "Check whether mailbox state was persisted without credential metadata.",
        ]
    if error_code == "credential_revoked":
        return [
            "Start reauth for this mailbox to create a fresh credential ref.",
            "Verify that the linked secret ref was not manually revoked.",
        ]
    if error_code == "credential_expired":
        return [
            "Reauth the mailbox to rotate credentials.",
            "Verify provider-side token/session validity.",
        ]
    if error_code == "missing_secret_ref":
        return [
            "Inspect credential ref binding and ensure a secret ref exists.",
            "Re-run auth completion if secret persistence failed.",
        ]
    if error_code == "secret_ref_missing":
        return [
            "Inspect secret storage for the linked secret ref id.",
            "Reauth the mailbox if the secret record cannot be recovered.",
        ]
    if error_code == "secret_ref_revoked":
        return [
            "Reauth the mailbox to issue a fresh secret ref.",
            "Audit why the previous secret ref was revoked.",
        ]
    if error_code == "unknown_mailbox_health":
        return [
            "Inspect mailbox diagnostics and OAuth session diagnostics for more detail.",
        ]
    return []


def build_mailbox_health(
    mailbox: ConnectedMailbox,
    credential_ref: MailboxCredentialRef | None = None,
    secret_descriptor: SecretDescriptor | None = None,
    *,
    last_error_code: str | None = None,
    last_error_safe_message: str | None = None,
) -> MailboxConnectionHealth:
    if mailbox.state == MailboxState.DISCONNECTED:
        health = "disconnected"
        error_code = last_error_code
        error_message = last_error_safe_message
    elif mailbox.state in {MailboxState.PENDING_AUTH, MailboxState.REAUTH_REQUIRED, MailboxState.TOKEN_EXPIRED}:
        health = "attention_required"
        error_code = last_error_code or "auth_incomplete"
        error_message = last_error_safe_message or "Mailbox requires authentication attention."
    elif mailbox.state == MailboxState.ACTIVE and credential_ref is None:
        health = "degraded"
        error_code = last_error_code or "missing_credential_ref"
        error_message = last_error_safe_message or "Mailbox is active but credential ref is missing."
    elif credential_ref and credential_ref.status == CredentialRefStatus.REVOKED:
        health = "degraded"
        error_code = last_error_code or "credential_revoked"
        error_message = last_error_safe_message or "Credential ref was revoked and mailbox needs reauth."
    elif credential_ref and credential_ref.status == CredentialRefStatus.EXPIRED:
        health = "attention_required"
        error_code = last_error_code or "credential_expired"
        error_message = last_error_safe_message or "Credential ref expired and mailbox needs reauth."
    elif credential_ref and credential_ref.secret_ref_id is None:
        health = "degraded"
        error_code = last_error_code or "missing_secret_ref"
        error_message = last_error_safe_message or "Credential ref exists but linked secret ref is missing."
    elif credential_ref and secret_descriptor is None:
        health = "degraded"
        error_code = last_error_code or "secret_ref_missing"
        error_message = last_error_safe_message or "Linked secret ref metadata could not be found."
    elif secret_descriptor and secret_descriptor.status != "ACTIVE":
        health = "attention_required"
        error_code = last_error_code or "secret_ref_revoked"
        error_message = last_error_safe_message or "Linked secret ref is not active."
    elif mailbox.state == MailboxState.ACTIVE and credential_ref and credential_ref.status == CredentialRefStatus.ACTIVE:
        health = "healthy"
        error_code = last_error_code
        error_message = last_error_safe_message
    else:
        health = "degraded"
        error_code = last_error_code or "unknown_mailbox_health"
        error_message = last_error_safe_message or "Mailbox health is degraded for an unknown safe reason."

    return MailboxConnectionHealth(
        mailbox_id=mailbox.mailbox_id,
        health_status=health,
        last_successful_auth_at=credential_ref.last_validated_at if credential_ref else None,
        last_failure_at=_now() if error_code and health != "healthy" else None,
        last_error_code=error_code,
        last_error_safe_message=error_message,
    )


def render_mailbox_status(
    mailbox: ConnectedMailbox,
    credential_ref: MailboxCredentialRef | None = None,
    secret_descriptor: SecretDescriptor | None = None,
) -> dict[str, object]:
    health = build_mailbox_health(mailbox, credential_ref, secret_descriptor)
    return {
        "mailbox": asdict(mailbox),
        "credential_ref": asdict(credential_ref) if credential_ref else None,
        "secret_descriptor": asdict(secret_descriptor) if secret_descriptor else None,
        "provider_account_id": mailbox.provider_account_id,
        "credential_provider_account_id": credential_ref.provider_account_id if credential_ref else None,
        "client_secret_ref_id": credential_ref.client_secret_ref_id if credential_ref else None,
        "health": asdict(health),
        "remediation_hints": remediation_hints_for_error(health.last_error_code),
    }


def render_mailbox_status_json(
    mailbox: ConnectedMailbox,
    credential_ref: MailboxCredentialRef | None = None,
    secret_descriptor: SecretDescriptor | None = None,
) -> str:
    return json.dumps(render_mailbox_status(mailbox, credential_ref, secret_descriptor), ensure_ascii=False)
