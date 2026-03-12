from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class OAuthConfig:
    authorization_url: str
    token_url: str
    redirect_uri: str
    scopes: list[str] = field(default_factory=list)
    use_pkce: bool = True


@dataclass(slots=True)
class OAuthStartResult:
    provider: str
    authorization_url: str
    state_token: str
    redirect_uri: str
    scopes: list[str]
    pkce_required: bool


@dataclass(slots=True)
class OAuthCompleteRequest:
    provider: str
    auth_session_id: str
    authorization_code: str
    state_token: str


@dataclass(slots=True)
class OAuthCompleteResult:
    provider: str
    mailbox_id: str
    credential_type: str
    state: str
