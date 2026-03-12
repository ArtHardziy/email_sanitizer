from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from onboarding_models import (
    AuthCompleteResult,
    ConnectMailboxResult,
    ConnectedMailbox,
    CredentialType,
    DisconnectMailboxResult,
    MailboxCredentialRef,
    MailboxState,
    OAuthAuthorizationSession,
    OnboardingInstruction,
)
from pathlib import Path

from gmail_oauth_backend import GmailOAuthBackend
from provider_presets import AuthMode, ProviderPreset, get_provider_preset


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _future(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def connect_mailbox(*, user_id: str, provider: str, email_address: str | None = None, display_name: str | None = None) -> ConnectMailboxResult:
    preset = get_provider_preset(provider)
    mailbox_id = f"mbx_{uuid4().hex[:12]}"
    mailbox = ConnectedMailbox(
        mailbox_id=mailbox_id,
        user_id=user_id,
        provider=preset.provider_id.value,
        display_name=display_name or preset.display_name,
        email_address=email_address or "",
        state=MailboxState.PENDING_AUTH,
        auth_mode=preset.preferred_auth_mode.value,
        created_at=_now(),
        updated_at=_now(),
    )

    instructions = [OnboardingInstruction(step=f"hint_{i+1}", details=hint) for i, hint in enumerate(preset.onboarding_hints)]

    auth_session = None
    if preset.preferred_auth_mode == AuthMode.OAUTH:
        if preset.provider_id.value == "gmail":
            backend = GmailOAuthBackend(Path('.state/email_sanitizer/oauth_sessions.json'))
            auth_session, oauth_start = backend.start(user_id=user_id, mailbox_label=display_name or preset.display_name)
            instructions.insert(0, OnboardingInstruction(step="oauth_start", details=f"Open authorization URL: {oauth_start.authorization_url}"))
        else:
            auth_session = OAuthAuthorizationSession(
                auth_session_id=f"oas_{uuid4().hex[:12]}",
                user_id=user_id,
                provider=preset.provider_id.value,
                mailbox_label=display_name or preset.display_name,
                status="PENDING",
                state_token=f"st_{uuid4().hex}",
                redirect_uri="https://backend.example.com/oauth/callback",
                created_at=_now(),
                expires_at=_future(15),
            )
            instructions.insert(0, OnboardingInstruction(step="oauth_start", details="Open the authorization URL and complete provider consent."))
    else:
        instructions.insert(0, OnboardingInstruction(step="credential_input", details="Provide provider-specific app password via the secure backend intake path."))

    return ConnectMailboxResult(mailbox=mailbox, instructions=instructions, auth_session=auth_session)


def complete_auth(*, mailbox: ConnectedMailbox, provider: str) -> AuthCompleteResult:
    preset = get_provider_preset(provider)
    credential_type = {
        AuthMode.OAUTH: CredentialType.OAUTH_REFRESH_TOKEN,
        AuthMode.XOAUTH2_IMAP: CredentialType.XOAUTH2_REFRESH_TOKEN,
        AuthMode.APP_PASSWORD: CredentialType.APP_PASSWORD,
        AuthMode.EXTERNAL_APP_PASSWORD: CredentialType.EXTERNAL_APP_PASSWORD,
    }[preset.preferred_auth_mode]

    mailbox.state = MailboxState.ACTIVE
    mailbox.updated_at = _now()
    credential_ref = MailboxCredentialRef(
        credential_ref_id=f"cred_{uuid4().hex[:12]}",
        mailbox_id=mailbox.mailbox_id,
        credential_type=credential_type,
        secret_ref_id=f"sec_{uuid4().hex[:12]}",
        status="ACTIVE",
        version=1,
        created_at=_now(),
    )
    mailbox.credential_ref_id = credential_ref.credential_ref_id
    return AuthCompleteResult(mailbox=mailbox, credential_ref=credential_ref)


def reauth_mailbox(mailbox: ConnectedMailbox) -> ConnectedMailbox:
    mailbox.state = MailboxState.REAUTH_REQUIRED
    mailbox.updated_at = _now()
    return mailbox


def disconnect_mailbox(mailbox: ConnectedMailbox) -> DisconnectMailboxResult:
    previous = mailbox.state
    mailbox.state = MailboxState.DISCONNECTED
    mailbox.updated_at = _now()
    return DisconnectMailboxResult(mailbox=mailbox, previous_state=previous)
