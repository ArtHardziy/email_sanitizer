from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from client_secret_registry import validate_provider_client_secret_ref, validate_provider_client_secret_runtime
from credential_registry import CredentialRegistry
from gmail_oauth_backend import GmailOAuthBackend
from mailbox_registry import MailboxRegistry
from oauth_models import OAuthCompleteRequest
from oauth_state_store import OAuthSessionStore
from onboarding_models import (
    AuthCompleteResult,
    ConnectMailboxResult,
    ConnectedMailbox,
    CredentialRefStatus,
    CredentialType,
    DisconnectMailboxResult,
    MailboxCredentialRef,
    MailboxState,
    OAuthAuthorizationSession,
    OAuthSessionStatus,
    OnboardingInstruction,
)
from provider_presets import AuthMode, get_provider_preset
from secret_manager import LocalSecretManager, SecretDescriptor


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _future(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def _default_state_dir() -> Path:
    return Path(".state/email_sanitizer")


def _credential_registry() -> CredentialRegistry:
    return CredentialRegistry(_default_state_dir() / "credential_refs.json")


def _mailbox_registry() -> MailboxRegistry:
    return MailboxRegistry(_default_state_dir() / "mailboxes.json")


def _oauth_session_store() -> OAuthSessionStore:
    return OAuthSessionStore(_default_state_dir() / "oauth_sessions.json")


def _secret_manager() -> LocalSecretManager:
    return LocalSecretManager(_default_state_dir() / "oauth_secrets.json")


def _start_mailbox_auth_session(mailbox: ConnectedMailbox) -> ConnectMailboxResult:
    preset = get_provider_preset(mailbox.provider)
    instructions = [OnboardingInstruction(step=f"hint_{i+1}", details=hint) for i, hint in enumerate(preset.onboarding_hints)]

    auth_session = None
    if preset.preferred_auth_mode == AuthMode.OAUTH:
        if preset.provider_id.value == "gmail":
            client_meta = validate_provider_client_secret_ref("gmail")
            runtime_meta = validate_provider_client_secret_runtime("gmail")
            instructions.insert(0, OnboardingInstruction(step="oauth_client", details=client_meta.safe_message))
            instructions.insert(1, OnboardingInstruction(step="oauth_client_runtime", details=runtime_meta.safe_message))
            backend = GmailOAuthBackend(_default_state_dir() / "oauth_sessions.json", secrets_path=_default_state_dir() / "oauth_secrets.json")
            auth_session, oauth_start = backend.start(
                user_id=mailbox.user_id,
                mailbox_id=mailbox.mailbox_id,
                mailbox_label=mailbox.display_name,
            )
            instructions.insert(2, OnboardingInstruction(step="oauth_start", details=f"Open authorization URL: {oauth_start.authorization_url}"))
            instructions.insert(3, OnboardingInstruction(step="oauth_session", details=f"Auth session id: {oauth_start.auth_session_id}; expires at: {oauth_start.expires_at}"))
        else:
            auth_session = OAuthAuthorizationSession(
                auth_session_id=f"oas_{uuid4().hex[:12]}",
                user_id=mailbox.user_id,
                provider=preset.provider_id.value,
                mailbox_label=mailbox.display_name or preset.display_name,
                mailbox_id=mailbox.mailbox_id,
                status=OAuthSessionStatus.CREATED,
                state_token=f"st_{uuid4().hex}",
                redirect_uri="https://backend.example.com/oauth/callback",
                created_at=_now(),
                expires_at=_future(15),
                auth_mode=preset.preferred_auth_mode.value,
            )
            instructions.insert(0, OnboardingInstruction(step="oauth_start", details="Open the authorization URL and complete provider consent."))
    else:
        instructions.insert(0, OnboardingInstruction(step="credential_input", details="Provide provider-specific app password via the secure backend intake path."))

    _mailbox_registry().put(mailbox)
    return ConnectMailboxResult(mailbox=mailbox, instructions=instructions, auth_session=auth_session)


def connect_mailbox(*, user_id: str, provider: str, email_address: str | None = None, display_name: str | None = None) -> ConnectMailboxResult:
    preset = get_provider_preset(provider)
    mailbox = ConnectedMailbox(
        mailbox_id=f"mbx_{uuid4().hex[:12]}",
        user_id=user_id,
        provider=preset.provider_id.value,
        display_name=display_name or preset.display_name,
        email_address=email_address or "",
        state=MailboxState.PENDING_AUTH,
        auth_mode=preset.preferred_auth_mode.value,
        created_at=_now(),
        updated_at=_now(),
    )
    return _start_mailbox_auth_session(mailbox)


def complete_auth(
    *,
    mailbox: ConnectedMailbox,
    provider: str,
    auth_session_id: str | None = None,
    state_token: str | None = None,
    authorization_code: str | None = None,
) -> AuthCompleteResult:
    preset = get_provider_preset(provider)
    credential_type = {
        AuthMode.OAUTH: CredentialType.OAUTH_REFRESH_TOKEN,
        AuthMode.XOAUTH2_IMAP: CredentialType.XOAUTH2_REFRESH_TOKEN,
        AuthMode.APP_PASSWORD: CredentialType.APP_PASSWORD,
        AuthMode.EXTERNAL_APP_PASSWORD: CredentialType.EXTERNAL_APP_PASSWORD,
    }[preset.preferred_auth_mode]

    secret_ref_id: str | None = f"sec_{uuid4().hex[:12]}"
    credential_ref_id: str = f"cred_{uuid4().hex[:12]}"
    provider_account_id: str | None = None
    client_secret_ref_id: str | None = None

    if preset.provider_id.value == "gmail":
        if not auth_session_id or not state_token or not authorization_code:
            raise ValueError("Gmail auth completion requires auth_session_id, state_token, and authorization_code")
        client_meta = validate_provider_client_secret_runtime("gmail")
        if not client_meta.ok:
            raise ValueError(client_meta.safe_message)
        backend = GmailOAuthBackend(_default_state_dir() / "oauth_sessions.json", secrets_path=_default_state_dir() / "oauth_secrets.json")
        oauth_result = backend.complete(
            req=OAuthCompleteRequest(
                provider=provider,
                auth_session_id=auth_session_id,
                authorization_code=authorization_code,
                state_token=state_token,
            ),
            mailbox_id=mailbox.mailbox_id,
        )
        credential_ref_id = oauth_result.credential_ref_id or credential_ref_id
        secret_ref_id = oauth_result.secret_ref_id
        provider_account_id = oauth_result.provider_account_id
        client_secret_ref_id = client_meta.client_secret_ref_id

    mailbox.state = MailboxState.ACTIVE
    mailbox.updated_at = _now()
    mailbox.provider_account_id = provider_account_id
    credential_ref = MailboxCredentialRef(
        credential_ref_id=credential_ref_id,
        mailbox_id=mailbox.mailbox_id,
        provider=provider,
        credential_type=credential_type,
        secret_ref_id=secret_ref_id,
        status=CredentialRefStatus.ACTIVE,
        version=1,
        created_at=_now(),
        updated_at=_now(),
        auth_mode=preset.preferred_auth_mode.value,
        provider_account_id=provider_account_id,
        client_secret_ref_id=client_secret_ref_id,
        last_validated_at=_now(),
    )
    mailbox.credential_ref_id = credential_ref.credential_ref_id
    _credential_registry().put(credential_ref)
    _mailbox_registry().put(mailbox)
    return AuthCompleteResult(mailbox=mailbox, credential_ref=credential_ref)


def reauth_mailbox(mailbox: ConnectedMailbox) -> ConnectedMailbox:
    mailbox.state = MailboxState.REAUTH_REQUIRED
    mailbox.updated_at = _now()
    _mailbox_registry().put(mailbox)
    return mailbox


def start_reauth_mailbox(mailbox: ConnectedMailbox) -> ConnectMailboxResult:
    mailbox = reauth_mailbox(mailbox)
    return _start_mailbox_auth_session(mailbox)


def get_mailbox(mailbox_id: str) -> ConnectedMailbox | None:
    return _mailbox_registry().get(mailbox_id)


def list_mailboxes_for_user(user_id: str) -> list[ConnectedMailbox]:
    return _mailbox_registry().list_for_user(user_id)


def get_mailbox_credential_ref(mailbox: ConnectedMailbox) -> MailboxCredentialRef | None:
    if not mailbox.credential_ref_id:
        return None
    return _credential_registry().get(mailbox.credential_ref_id)


def update_mailbox_credential_ref(mailbox: ConnectedMailbox, credential_ref: MailboxCredentialRef) -> None:
    mailbox.credential_ref_id = credential_ref.credential_ref_id
    mailbox.updated_at = _now()
    _credential_registry().put(credential_ref)
    _mailbox_registry().put(mailbox)


def revoke_mailbox_secret(mailbox: ConnectedMailbox) -> SecretDescriptor | None:
    credential_ref = get_mailbox_credential_ref(mailbox)
    if not credential_ref or not credential_ref.secret_ref_id:
        return None
    descriptor = _secret_manager().revoke_secret(credential_ref.secret_ref_id)
    mailbox.state = MailboxState.REAUTH_REQUIRED
    mailbox.updated_at = _now()
    _mailbox_registry().put(mailbox)
    return descriptor


def rotate_mailbox_secret(mailbox: ConnectedMailbox, *, new_secret_value: str) -> SecretDescriptor | None:
    credential_ref = get_mailbox_credential_ref(mailbox)
    if not credential_ref or not credential_ref.secret_ref_id:
        return None
    descriptor = _secret_manager().rotate_secret(credential_ref.secret_ref_id, new_secret_value=new_secret_value)
    credential_ref.secret_ref_id = descriptor.secret_ref_id
    credential_ref.updated_at = _now()
    credential_ref.last_validated_at = _now()
    update_mailbox_credential_ref(mailbox, credential_ref)
    mailbox.state = MailboxState.ACTIVE
    mailbox.updated_at = _now()
    _mailbox_registry().put(mailbox)
    return descriptor


def list_oauth_sessions_for_mailbox(mailbox_id: str) -> list[OAuthAuthorizationSession]:
    return [session for session in _oauth_session_store().list_all() if session.mailbox_id == mailbox_id]


def get_mailbox_secret_descriptor(mailbox: ConnectedMailbox) -> SecretDescriptor | None:
    credential_ref = get_mailbox_credential_ref(mailbox)
    if not credential_ref or not credential_ref.secret_ref_id:
        return None
    try:
        return _secret_manager().describe_secret(credential_ref.secret_ref_id)
    except ValueError:
        return None


def disconnect_mailbox(mailbox: ConnectedMailbox) -> DisconnectMailboxResult:
    previous = mailbox.state
    mailbox.state = MailboxState.DISCONNECTED
    mailbox.updated_at = _now()
    _mailbox_registry().put(mailbox)
    return DisconnectMailboxResult(mailbox=mailbox, previous_state=previous)
