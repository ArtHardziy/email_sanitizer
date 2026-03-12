from __future__ import annotations

import json

from provider_presets import PRESETS


if __name__ == "__main__":
    print(json.dumps(
        {
            key.value: {
                "displayName": preset.display_name,
                "imapHost": preset.imap_host,
                "imapPort": preset.imap_port,
                "useSsl": preset.use_ssl,
                "preferredAuthMode": preset.preferred_auth_mode.value,
                "allowedAuthModes": [mode.value for mode in preset.allowed_auth_modes],
            }
            for key, preset in PRESETS.items()
        },
        ensure_ascii=False,
        indent=2,
    ))
