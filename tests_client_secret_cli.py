from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_client_secret_cli_put_and_validate() -> None:
    cli_path = Path(__file__).with_name("client_secret_cli.py")
    put_out = subprocess.check_output([
        "python",
        str(cli_path),
        "put-gmail-client-secret",
        "--value",
        "demo-client-secret",
        "--replace",
    ], text=True)
    put_data = json.loads(put_out)
    assert put_data["secret_ref_id"] == "sec_google_oauth_client_secret"

    validate_out = subprocess.check_output([
        "python",
        str(cli_path),
        "validate-gmail-client-secret",
    ], text=True)
    validate_data = json.loads(validate_out)
    assert validate_data["ok"] is True
    assert validate_data["client_secret_ref_id"] == "sec_google_oauth_client_secret"


def run_tests() -> None:
    tests = [test_client_secret_cli_put_and_validate]
    for test in tests:
        test()
    print(f"ok: {len(tests)} client secret cli tests passed")


if __name__ == "__main__":
    run_tests()
