from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass(slots=True)
class SecretRecord:
    secret_ref_id: str
    provider: str
    secret_type: str
    status: str
    created_at: str
    updated_at: str
    revoked_at: str | None = None
    superseded_by_secret_ref_id: str | None = None
    value: str | None = None


@dataclass(slots=True)
class SecretDescriptor:
    secret_ref_id: str
    provider: str
    secret_type: str
    status: str
    created_at: str
    updated_at: str
    revoked_at: str | None = None
    superseded_by_secret_ref_id: str | None = None


class LocalSecretManager:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load_all(self) -> dict[str, SecretRecord]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        records: dict[str, SecretRecord] = {}
        for item in raw.get("secrets", []):
            records[item["secret_ref_id"]] = SecretRecord(**item)
        return records

    def _save_all(self, records: dict[str, SecretRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"secrets": [asdict(v) for v in records.values()]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def put_secret(self, *, provider: str, secret_type: str, secret_value: str) -> SecretDescriptor:
        now = self._now()
        record = SecretRecord(
            secret_ref_id=f"sec_{uuid4().hex[:12]}",
            provider=provider,
            secret_type=secret_type,
            status="ACTIVE",
            created_at=now,
            updated_at=now,
            value=secret_value,
        )
        records = self._load_all()
        records[record.secret_ref_id] = record
        self._save_all(records)
        return self.describe_secret(record.secret_ref_id)

    def put_secret_with_ref(self, *, secret_ref_id: str, provider: str, secret_type: str, secret_value: str, replace: bool = False) -> SecretDescriptor:
        records = self._load_all()
        existing = records.get(secret_ref_id)
        now = self._now()
        if existing and not replace and existing.status == "ACTIVE":
            raise ValueError("Secret ref already exists and is active")
        records[secret_ref_id] = SecretRecord(
            secret_ref_id=secret_ref_id,
            provider=provider,
            secret_type=secret_type,
            status="ACTIVE",
            created_at=existing.created_at if existing else now,
            updated_at=now,
            revoked_at=None,
            superseded_by_secret_ref_id=None,
            value=secret_value,
        )
        self._save_all(records)
        return self.describe_secret(secret_ref_id)

    def get_secret_for_backend(self, secret_ref_id: str) -> str:
        record = self._load_all().get(secret_ref_id)
        if not record:
            raise ValueError("Secret ref not found")
        if record.status != "ACTIVE" or record.revoked_at is not None or not record.value:
            raise ValueError("Secret ref is not active")
        return record.value

    def describe_secret(self, secret_ref_id: str) -> SecretDescriptor:
        record = self._load_all().get(secret_ref_id)
        if not record:
            raise ValueError("Secret ref not found")
        return SecretDescriptor(
            secret_ref_id=record.secret_ref_id,
            provider=record.provider,
            secret_type=record.secret_type,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            revoked_at=record.revoked_at,
            superseded_by_secret_ref_id=record.superseded_by_secret_ref_id,
        )

    def revoke_secret(self, secret_ref_id: str) -> SecretDescriptor:
        records = self._load_all()
        record = records.get(secret_ref_id)
        if not record:
            raise ValueError("Secret ref not found")
        now = self._now()
        record.status = "REVOKED"
        record.revoked_at = now
        record.updated_at = now
        record.value = None
        records[secret_ref_id] = record
        self._save_all(records)
        return self.describe_secret(secret_ref_id)

    def rotate_secret(self, secret_ref_id: str, *, new_secret_value: str) -> SecretDescriptor:
        records = self._load_all()
        record = records.get(secret_ref_id)
        if not record:
            raise ValueError("Secret ref not found")
        now = self._now()
        new_record = SecretRecord(
            secret_ref_id=f"sec_{uuid4().hex[:12]}",
            provider=record.provider,
            secret_type=record.secret_type,
            status="ACTIVE",
            created_at=now,
            updated_at=now,
            value=new_secret_value,
        )
        record.status = "REVOKED"
        record.revoked_at = now
        record.updated_at = now
        record.superseded_by_secret_ref_id = new_record.secret_ref_id
        record.value = None
        records[secret_ref_id] = record
        records[new_record.secret_ref_id] = new_record
        self._save_all(records)
        return self.describe_secret(new_record.secret_ref_id)
