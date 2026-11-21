import json
from pathlib import Path

from app.shared.contracts import AuditEntry
from app.storage.db import Database


class AuditLog:
    """In-memory buffer + Neon write-through; JSONL mirror when a path is set."""

    def __init__(
        self, db: Database | None = None, jsonl_path: Path | None = None
    ) -> None:
        self._entries: list[AuditEntry] = []
        self._db = db
        self._jsonl_path = jsonl_path

    def append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)
        if self._db is not None:
            self._db.append_audit(
                entry.incident_id,
                entry.actor_id,
                entry.actor_role.value,
                entry.action.value,
                entry.outcome,
            )
        if self._jsonl_path is not None:
            with self._jsonl_path.open("a") as fh:
                fh.write(json.dumps(entry.model_dump(mode="json")) + "\n")

    def for_incident(self, incident_id: str) -> list[AuditEntry]:
        return [entry for entry in self._entries if str(entry.incident_id) == incident_id]
