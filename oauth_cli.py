from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from gmail_oauth_backend import GmailOAuthBackend
from oauth_diagnostics import build_oauth_session_diagnostic


def _backend() -> GmailOAuthBackend:
    state_dir = Path(".state/email_sanitizer")
    return GmailOAuthBackend(state_dir / "oauth_sessions.json", secrets_path=state_dir / "oauth_secrets.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="OAuth diagnostics CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    session = sub.add_parser("session")
    session.add_argument("--auth-session-id", required=True)

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--provider", default="gmail")

    cleanup = sub.add_parser("cleanup")
    cleanup.add_argument("--provider", default="gmail")

    args = parser.parse_args()
    backend = _backend()

    if args.command == "session":
        session_obj = backend.get_session(args.auth_session_id)
        if not session_obj:
            raise SystemExit("OAuth session not found")
        print(json.dumps(asdict(build_oauth_session_diagnostic(session_obj)), ensure_ascii=False))
        return

    if args.command == "list":
        print(json.dumps([
            asdict(build_oauth_session_diagnostic(session_obj))
            for session_obj in backend.list_sessions()
            if session_obj.provider == args.provider
        ], ensure_ascii=False))
        return

    if args.command == "cleanup":
        cleaned = backend.cleanup_expired_sessions()
        print(json.dumps({"cleaned_session_ids": cleaned, "count": len(cleaned)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
