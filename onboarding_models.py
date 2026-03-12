from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MailboxState(str, Enum):
    PENDING_AUTH = "PENDING_AUTH"
    ACTIVE = "ACTIVE"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    REAUTH_REQUIRED = "REAUTH_REQUIRED"
    ACCESS_REVOKED = "ACCESS_REVOKED"
    SYNC_DEGRADED = "SYNC_DEGRADED"
    DISCONNECTED = "DISCONNECTED"


class CredentialType(str, Enum):
    OAUTH_REFRESH_TOKEN = "oauth_refresh_token"
    APP_PASSWORD = "app_password"
    EXTERNAL_APP_PASSWORD = "external_app_password"
    XOAUTH2_REFRESH_TOKEN = "xoauth2_refresh_token"


@dataclass(slots=True)
class ConnectedMailbox:
    mailbox_id: str
    user_id: str
    provider: str
    display_name: str
    email_address: str
    state: MailboxState
    auth_mode: str
    created_at: str
    updated_at: str
    credential_ref_id: str | None = None


@dataclass(slots=True)
class MailboxCredentialRef:
    credential_ref_id: str
    mailbox_id: str
    credential_type: CredentialType
    secret_ref_id: str | None
    status: str
    version: int
    created_at: str


@dataclass(slots=True)
class OAuthAuthorizationSession:
    auth_session_id: str
    user_id: str
    provider: str
    mailbox_label: str | None
    status: str
    state_token: str
    redirect_uri: str
    created_at: str
    expires_at: str


@dataclass(slots=True)
class MailboxConnectionHealth:
    mailbox_id: str
    health_status: str
    last_successful_auth_at: str | None = None
    last_successful_sync_at: str | None = None
    last_failure_at: str | None = None
    failure_count_window: int = 0
    consecutive_failures: int = 0
    last_error_code: str | None = None
    last_error_safe_message: str | None = None


@dataclass(slots=True)
class ProviderAccountCapability:
    mailbox_id: str
    provider: str
    supports_oauth: bool
    supports_app_password: bool
    supports_external_app_password: bool
    supports_imap: bool
    supports_mark_seen: bool
    checked_at: str


@dataclass(slots=True)
class OnboardingInstruction:
    step: str
    details: str


@dataclass(slots=True)
class ConnectMailboxResult:
    mailbox: ConnectedMailbox
    instructions: list[OnboardingInstruction] = field(default_factory=list)
    auth_session: OAuthAuthorizationSession | None = None


@dataclass(slots=True)
class AuthCompleteResult:
    mailbox: ConnectedMailbox
    credential_ref: MailboxCredentialRef | None = None


@dataclass(slots=True)
class DisconnectMailboxResult:
    mailbox: ConnectedMailbox
    previous_state: MailboxState
