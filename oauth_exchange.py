from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenExchangeMode(str, Enum):
    MOCK = "mock"
    LIVE_BOUNDARY = "live_boundary"


@dataclass(slots=True)
class TokenExchangeRequest:
    provider: str
    authorization_code: str
    redirect_uri: str
    client_id: str
    client_secret_ref_id: str | None = None
    code_verifier: str | None = None
    callback_uri: str | None = None
    token_endpoint_auth_method: str = "client_secret_post"


@dataclass(slots=True)
class TokenExchangeResult:
    provider: str
    token_type: str
    refresh_token: str
    access_token_present: bool
    scope: str | None = None
    provider_account_id: str | None = None
    exchange_mode: str = TokenExchangeMode.MOCK.value


class GmailTokenExchangeService:
    mode = TokenExchangeMode.MOCK

    def exchange_code(self, req: TokenExchangeRequest) -> TokenExchangeResult:
        if not req.authorization_code:
            raise ValueError("Authorization code is required")
        if req.provider != "gmail":
            raise ValueError("Unsupported provider for Gmail token exchange service")
        if not req.client_id:
            raise ValueError("OAuth client_id is required")
        return TokenExchangeResult(
            provider="gmail",
            token_type="Bearer",
            refresh_token=f"refresh::gmail::{req.authorization_code}",
            access_token_present=True,
            scope="https://mail.google.com/ openid email",
            provider_account_id="gmail-account-demo",
            exchange_mode=self.mode.value,
        )


class GmailLiveTokenExchangeBoundary(GmailTokenExchangeService):
    mode = TokenExchangeMode.LIVE_BOUNDARY

    def exchange_code(self, req: TokenExchangeRequest) -> TokenExchangeResult:
        if not req.client_secret_ref_id:
            raise ValueError("Live boundary requires client_secret_ref_id")
        if not req.callback_uri:
            raise ValueError("Live boundary requires callback_uri")
        return TokenExchangeResult(
            provider="gmail",
            token_type="Bearer",
            refresh_token=f"live-boundary::gmail::{req.authorization_code}",
            access_token_present=True,
            scope="https://mail.google.com/ openid email",
            provider_account_id="gmail-live-boundary-account",
            exchange_mode=self.mode.value,
        )
