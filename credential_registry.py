from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from onboarding_models import CredentialRefStatus, CredentialType, MailboxCredentialRef


class CredentialRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _normalize_ref(self, item: dict[str, object]) -> MailboxCredentialRef:
        normalized = dict(item)
        normalized["credential_type"] = CredentialType(normalized["credential_type"])
        normalized["status"] = CredentialRefStatus(normalized["status"])
        return MailboxCredentialRef(**normalized)

    def _load_all(self) -> dict[str, MailboxCredentialRef]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        refs: dict[str, MailboxCredentialRef] = {}
        for item in raw.get("credential_refs", []):
            ref = self._normalize_ref(item)
            refs[ref.credential_ref_id] = ref
        return refs

    def _save_all(self, refs: dict[str, MailboxCredentialRef]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"credential_refs": [asdict(v) for v in refs.values()]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def put(self, ref: MailboxCredentialRef) -> None:
        refs = self._load_all()
        refs[ref.credential_ref_id] = ref
        self._save_all(refs)

    def get(self, credential_ref_id: str) -> MailboxCredentialRef | None:
        return self._load_all().get(credential_ref_id)

    def list_for_mailbox(self, mailbox_id: str) -> list[MailboxCredentialRef]:
        return [ref for ref in self._load_all().values() if ref.mailbox_id == mailbox_id]
