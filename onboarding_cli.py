from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from onboarding_service import complete_auth, connect_mailbox, disconnect_mailbox, reauth_mailbox
from onboarding_models import ConnectedMailbox, MailboxState


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

    reauth = sub.add_parser("reauth")
    reauth.add_argument("--user-id", required=True)
    reauth.add_argument("--mailbox-id", required=True)
    reauth.add_argument("--provider", required=True)
    reauth.add_argument("--email", default="")
    reauth.add_argument("--display-name", required=True)

    disconnect = sub.add_parser("disconnect")
    disconnect.add_argument("--user-id", required=True)
    disconnect.add_argument("--mailbox-id", required=True)
    disconnect.add_argument("--provider", required=True)
    disconnect.add_argument("--email", default="")
    disconnect.add_argument("--display-name", required=True)

    args = parser.parse_args()

    if args.command == "connect":
        result = connect_mailbox(user_id=args.user_id, provider=args.provider, email_address=args.email, display_name=args.display_name)
        print(json.dumps(asdict(result), ensure_ascii=False))
        return

    mailbox = ConnectedMailbox(
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

    if args.command == "auth-complete":
        result = complete_auth(mailbox=mailbox, provider=args.provider)
        print(json.dumps(asdict(result), ensure_ascii=False))
    elif args.command == "reauth":
        result = reauth_mailbox(mailbox)
        print(json.dumps(asdict(result), ensure_ascii=False))
    elif args.command == "disconnect":
        result = disconnect_mailbox(mailbox)
        print(json.dumps(asdict(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
