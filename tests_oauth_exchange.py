from __future__ import annotations

from oauth_exchange import GmailLiveTokenExchangeBoundary, GmailTokenExchangeService, TokenExchangeMode, TokenExchangeRequest


def test_gmail_token_exchange_service_returns_refresh_token() -> None:
    service = GmailTokenExchangeService()
    result = service.exchange_code(TokenExchangeRequest(
        provider="gmail",
        authorization_code="code-123",
        redirect_uri="https://backend.example.com/oauth/google/callback",
        client_id="BACKEND_CONFIGURED_CLIENT_ID",
        client_secret_ref_id="sec_google_oauth_client_secret",
        code_verifier="verifier-123",
        callback_uri="https://backend.example.com/oauth/google/callback",
        token_endpoint_auth_method="client_secret_post",
    ))
    assert result.provider == "gmail"
    assert result.refresh_token.startswith("refresh::gmail::")
    assert result.access_token_present is True
    assert result.provider_account_id == "gmail-account-demo"
    assert result.exchange_mode == TokenExchangeMode.MOCK.value


def test_gmail_live_boundary_exchange_shape() -> None:
    service = GmailLiveTokenExchangeBoundary()
    result = service.exchange_code(TokenExchangeRequest(
        provider="gmail",
        authorization_code="code-123",
        redirect_uri="https://backend.example.com/oauth/google/callback",
        client_id="BACKEND_CONFIGURED_CLIENT_ID",
        client_secret_ref_id="sec_google_oauth_client_secret",
        code_verifier="verifier-123",
        callback_uri="https://backend.example.com/oauth/google/callback",
        token_endpoint_auth_method="client_secret_post",
    ))
    assert result.provider_account_id == "gmail-live-boundary-account"
    assert result.exchange_mode == TokenExchangeMode.LIVE_BOUNDARY.value


def run_tests() -> None:
    tests = [test_gmail_token_exchange_service_returns_refresh_token, test_gmail_live_boundary_exchange_shape]
    for test in tests:
        test()
    print(f"ok: {len(tests)} oauth exchange tests passed")


if __name__ == "__main__":
    run_tests()
