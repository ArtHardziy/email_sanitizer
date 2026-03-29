from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from diagnostics import diagnose_combined, diagnose_onboarding_state, diagnose_runtime, diagnostic_to_json
from runtime_loader import load_runtimes_from_config
from validation import validate_mailbox_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Email sanitizer local CLI")
    parser.add_argument("command", choices=["validate", "diagnose", "onboarding-diagnose"], help="Command to run")
    parser.add_argument("--config", default=str(Path(__file__).with_name("sample_config.json")), help="Path to config JSON")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    runtimes = load_runtimes_from_config(args.config)

    if args.command == "validate":
        reports = [validate_mailbox_config(runtime.mailbox) for runtime in runtimes]
        if args.json:
            print(json.dumps([
                {
                    "mailbox": report.mailbox_name,
                    "ok": report.ok,
                    "issues": [issue.__dict__ for issue in report.issues],
                }
                for report in reports
            ], ensure_ascii=False))
        else:
            for report in reports:
                print(f"[{report.mailbox_name}] ok={report.ok} issues={len(report.issues)}")
                for issue in report.issues:
                    print(f"- {issue.level} {issue.field}: {issue.message}")
        return

    if args.command == "onboarding-diagnose":
        diagnostics = diagnose_onboarding_state()
        if args.json:
            print(json.dumps([asdict(diag) for diag in diagnostics], ensure_ascii=False))
        else:
            for diag in diagnostics:
                print(json.dumps(asdict(diag), ensure_ascii=False))
        return

    if args.command == "diagnose":
        diagnostics = [diagnose_combined(runtime) for runtime in runtimes]
        if args.json:
            print(json.dumps([asdict(diag) for diag in diagnostics], ensure_ascii=False))
        else:
            for diag in diagnostics:
                print(json.dumps(asdict(diag), ensure_ascii=False))


if __name__ == "__main__":
    main()
