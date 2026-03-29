from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from onboarding_models import OAuthAuthorizationSession, OAuthSessionStatus


class OAuthSessionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _normalize_session(self, item: dict[str, object]) -> OAuthAuthorizationSession:
        normalized = dict(item)
        normalized["status"] = OAuthSessionStatus(normalized["status"])
        return OAuthAuthorizationSession(**normalized)

    def load_all(self) -> dict[str, OAuthAuthorizationSession]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        result: dict[str, OAuthAuthorizationSession] = {}
        for item in raw.get("sessions", []):
            session = self._normalize_session(item)
            result[session.auth_session_id] = session
        return result

    def save_all(self, sessions: dict[str, OAuthAuthorizationSession]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"sessions": [asdict(v) for v in sessions.values()]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def put(self, session: OAuthAuthorizationSession) -> None:
        sessions = self.load_all()
        sessions[session.auth_session_id] = session
        self.save_all(sessions)

    def get(self, auth_session_id: str) -> OAuthAuthorizationSession | None:
        return self.load_all().get(auth_session_id)

    def update(self, session: OAuthAuthorizationSession) -> None:
        self.put(session)

    def delete(self, auth_session_id: str) -> None:
        sessions = self.load_all()
        if auth_session_id in sessions:
            del sessions[auth_session_id]
            self.save_all(sessions)

    def list_all(self) -> list[OAuthAuthorizationSession]:
        return list(self.load_all().values())

    def list_expired(self, *, now_iso: str) -> list[OAuthAuthorizationSession]:
        return [session for session in self.load_all().values() if session.expires_at <= now_iso]
