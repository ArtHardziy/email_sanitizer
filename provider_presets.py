from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from config import MailboxConfig
from oauth_models import OAuthClientConfig, OAuthConfig


class ProviderId(str, Enum):
    GMAIL = "gmail"
    YANDEX = "yandex"
    MAILRU = "mailru"
    ICLOUD = "icloud"


class AuthMode(str, Enum):
    OAUTH = "oauth"
    APP_PASSWORD = "app_password"
    EXTERNAL_APP_PASSWORD = "external_app_password"
    XOAUTH2_IMAP = "xoauth2_imap"


@dataclass(slots=True)
class ProviderPreset:
    provider_id: ProviderId
    display_name: str
    imap_host: str
    imap_port: int
    use_ssl: bool
    preferred_auth_mode: AuthMode
    allowed_auth_modes: list[AuthMode]
    onboarding_hints: list[str]
    oauth_config: OAuthConfig | None = None
    supports_incremental_sync: bool = True
    supports_mark_seen: bool = True


PRESETS: dict[ProviderId, ProviderPreset] = {
    ProviderId.GMAIL: ProviderPreset(
        provider_id=ProviderId.GMAIL,
        display_name="Gmail",
        imap_host="imap.gmail.com",
        imap_port=993,
        use_ssl=True,
        preferred_auth_mode=AuthMode.OAUTH,
        allowed_auth_modes=[AuthMode.OAUTH, AuthMode.XOAUTH2_IMAP],
        onboarding_hints=[
            "Use OAuth 2.0 as the primary authentication path.",
            "Preserve abstraction so IMAP XOAUTH2 can later be swapped for Gmail API without breaking the domain model.",
            "Client secret must stay in backend secret storage; only client metadata should surface outside.",
        ],
        oauth_config=OAuthConfig(
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            redirect_uri="https://backend.example.com/oauth/google/callback",
            scopes=[
                "https://mail.google.com/",
                "openid",
                "email",
            ],
            use_pkce=True,
            client_config=OAuthClientConfig(
                client_id="BACKEND_CONFIGURED_CLIENT_ID",
                client_secret_ref_id="sec_google_oauth_client_secret",
                token_endpoint_auth_method="client_secret_post",
            ),
        ),
    ),
    ProviderId.YANDEX: ProviderPreset(
        provider_id=ProviderId.YANDEX,
        display_name="Yandex",
        imap_host="imap.yandex.com",
        imap_port=993,
        use_ssl=True,
        preferred_auth_mode=AuthMode.OAUTH,
        allowed_auth_modes=[AuthMode.OAUTH, AuthMode.APP_PASSWORD],
        onboarding_hints=[
            "Prefer OAuth as the primary path.",
            "Be ready for IMAP access to require enablement in account settings.",
        ],
    ),
    ProviderId.MAILRU: ProviderPreset(
        provider_id=ProviderId.MAILRU,
        display_name="Mail.ru",
        imap_host="imap.mail.ru",
        imap_port=993,
        use_ssl=True,
        preferred_auth_mode=AuthMode.EXTERNAL_APP_PASSWORD,
        allowed_auth_modes=[AuthMode.EXTERNAL_APP_PASSWORD],
        onboarding_hints=[
            "Use external app password only; never request the main account password.",
            "Be ready to classify external access disabled errors.",
        ],
    ),
    ProviderId.ICLOUD: ProviderPreset(
        provider_id=ProviderId.ICLOUD,
        display_name="iCloud",
        imap_host="imap.mail.me.com",
        imap_port=993,
        use_ssl=True,
        preferred_auth_mode=AuthMode.APP_PASSWORD,
        allowed_auth_modes=[AuthMode.APP_PASSWORD],
        onboarding_hints=[
            "Use Apple app-specific password only.",
            "Do not request or store the main Apple Account password.",
        ],
    ),
}


def get_provider_preset(provider: str | ProviderId) -> ProviderPreset:
    provider_id = ProviderId(provider)
    return PRESETS[provider_id]


def apply_provider_preset(mailbox: MailboxConfig, provider: str | ProviderId) -> MailboxConfig:
    preset = get_provider_preset(provider)
    return replace(
        mailbox,
        provider=preset.provider_id.value,
        host=preset.imap_host,
        port=preset.imap_port,
        use_ssl=preset.use_ssl,
    )


def supported_providers() -> list[str]:
    return [preset.provider_id.value for preset in PRESETS.values()]
