from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from mailbox_status import render_mailbox_status
from onboarding_models import ConnectedMailbox, MailboxState
from onboarding_service import (
    complete_auth,
    connect_mailbox,
    disconnect_mailbox,
    get_mailbox,
    get_mailbox_credential_ref,
    get_mailbox_secret_descriptor,
    list_mailboxes_for_user,
    reauth_mailbox,
    revoke_mailbox_secret,
    rotate_mailbox_secret,
    start_reauth_mailbox,
)


def _fallback_mailbox(args: argparse.Namespace) -> ConnectedMailbox:
    return ConnectedMailbox(
        mailbox_id=args.mailbox_id,
        user_id=args.user_id,
        provider=args.provider,
        display_name=args.display_name,
        email_address=args.email,
        state=MailboxState.PENDING_AUTH,
        auth_mode="",
        created_at="",
        updated_at="",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Mailbox onboarding CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    connect = sub.add_parser("connect")
    connect.add_argument("provider")
    connect.add_argument("--user-id", required=True)
    connect.add_argument("--email")
    connect.add_argument("--display-name")

    complete = sub.add_parser("auth-complete")
    complete.add_argument("provider")
    complete.add_argument("--user-id", required=True)
    complete.add_argument("--mailbox-id", required=True)
    complete.add_argument("--email", default="")
    complete.add_argument("--display-name", required=True)
    complete.add_argument("--auth-session-id")
    complete.add_argument("--state-token")
    complete.add_argument("--authorization-code")

    reauth = sub.add_parser("reauth")
    reauth.add_argument("--user-id", required=True)
    reauth.add_argument("--mailbox-id", required=True)
    reauth.add_argument("--provider", required=True)
    reauth.add_argument("--email", default="")
    reauth.add_argument("--display-name", required=True)

    reauth_start = sub.add_parser("reauth-start")
    reauth_start.add_argument("--mailbox-id", required=True)

    revoke_secret = sub.add_parser("revoke-secret")
    revoke_secret.add_argument("--mailbox-id", required=True)

    rotate_secret = sub.add_parser("rotate-secret")
    rotate_secret.add_argument("--mailbox-id", required=True)
    rotate_secret.add_argument("--new-secret-value", required=True)

    disconnect = sub.add_parser("disconnect")
    disconnect.add_argument("--user-id", required=True)
    disconnect.add_argument("--mailbox-id", required=True)
    disconnect.add_argument("--provider", required=True)
    disconnect.add_argument("--email", default="")
    disconnect.add_argument("--display-name", required=True)

    status = sub.add_parser("status")
    status.add_argument("--mailbox-id", required=True)

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--user-id", required=True)

    args = parser.parse_args()

    if args.command == "connect":
        result = connect_mailbox(user_id=args.user_id, provider=args.provider, email_address=args.email, display_name=args.display_name)
        print(json.dumps(asdict(result), ensure_ascii=False))
        return

    if args.command == "list":
        print(json.dumps([asdict(mailbox) for mailbox in list_mailboxes_for_user(args.user_id)], ensure_ascii=False))
        return

    if args.command == "status":
        mailbox = get_mailbox(args.mailbox_id)
        if not mailbox:
            raise SystemExit("Mailbox not found")
        credential_ref = get_mailbox_credential_ref(mailbox)
        secret_descriptor = get_mailbox_secret_descriptor(mailbox)
        print(json.dumps(render_mailbox_status(mailbox, credential_ref, secret_descriptor), ensure_ascii=False))
        return

    mailbox = get_mailbox(args.mailbox_id) or _fallback_mailbox(args)

    if args.command == "auth-complete":
        result = complete_auth(
            mailbox=mailbox,
            provider=args.provider,
            auth_session_id=args.auth_session_id,
            state_token=args.state_token,
            authorization_code=args.authorization_code,
        )
        print(json.dumps(asdict(result), ensure_ascii=False))
    elif args.command == "reauth":
        result = reauth_mailbox(mailbox)
        print(json.dumps(asdict(result), ensure_ascii=False))
    elif args.command == "reauth-start":
        result = start_reauth_mailbox(mailbox)
        print(json.dumps(asdict(result), ensure_ascii=False))
    elif args.command == "revoke-secret":
        result = revoke_mailbox_secret(mailbox)
        print(json.dumps(asdict(result) if result else None, ensure_ascii=False))
    elif args.command == "rotate-secret":
        result = rotate_mailbox_secret(mailbox, new_secret_value=args.new_secret_value)
        print(json.dumps(asdict(result) if result else None, ensure_ascii=False))
    elif args.command == "disconnect":
        result = disconnect_mailbox(mailbox)
        print(json.dumps(asdict(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
