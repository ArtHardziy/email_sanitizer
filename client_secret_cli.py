from __future__ import annotations

import argparse
import getpass
import json
from dataclasses import asdict
from pathlib import Path

from client_secret_registry import validate_provider_client_secret_runtime
from secret_manager import LocalSecretManager

DEFAULT_SECRET_REF_ID = "sec_google_oauth_client_secret"
DEFAULT_SECRETS_PATH = Path(".state/email_sanitizer/oauth_secrets.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision provider client secrets into local secret storage")
    sub = parser.add_subparsers(dest="command", required=True)

    put = sub.add_parser("put-gmail-client-secret")
    put.add_argument("--secret-ref-id", default=DEFAULT_SECRET_REF_ID)
    put.add_argument("--replace", action="store_true")
    put.add_argument("--value")

    validate = sub.add_parser("validate-gmail-client-secret")

    args = parser.parse_args()
    manager = LocalSecretManager(DEFAULT_SECRETS_PATH)

    if args.command == "put-gmail-client-secret":
        value = args.value or getpass.getpass("Paste Gmail OAuth client secret (input hidden): ")
        descriptor = manager.put_secret_with_ref(
            secret_ref_id=args.secret_ref_id,
            provider="gmail",
            secret_type="provider_client_secret",
            secret_value=value,
            replace=args.replace,
        )
        print(json.dumps(asdict(descriptor), ensure_ascii=False))
        return

    if args.command == "validate-gmail-client-secret":
        result = validate_provider_client_secret_runtime("gmail", secrets_path=DEFAULT_SECRETS_PATH)
        print(json.dumps(asdict(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
