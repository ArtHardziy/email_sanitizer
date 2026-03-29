from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class OAuthClientConfig:
    client_id: str
    client_secret_ref_id: str | None = None
    token_endpoint_auth_method: str = "client_secret_post"


@dataclass(slots=True)
class OAuthConfig:
    authorization_url: str
    token_url: str
    redirect_uri: str
    scopes: list[str] = field(default_factory=list)
    use_pkce: bool = True
    client_config: OAuthClientConfig | None = None


@dataclass(slots=True)
class OAuthStartResult:
    provider: str
    authorization_url: str
    state_token: str
    redirect_uri: str
    scopes: list[str]
    pkce_required: bool
    auth_session_id: str | None = None
    expires_at: str | None = None
    client_id: str | None = None


@dataclass(slots=True)
class OAuthCallbackPayload:
    provider: str
    callback_uri: str
    state_token: str
    authorization_code: str
    scope: str | None = None
    prompt: str | None = None
    error: str | None = None
    error_description: str | None = None


@dataclass(slots=True)
class OAuthCompleteRequest:
    provider: str
    auth_session_id: str
    authorization_code: str
    state_token: str
    callback_uri: str | None = None


@dataclass(slots=True)
class OAuthCompleteResult:
    provider: str
    mailbox_id: str
    credential_type: str
    state: str
    credential_ref_id: str | None = None
    secret_ref_id: str | None = None
    session_status: str | None = None
    provider_account_id: str | None = None
