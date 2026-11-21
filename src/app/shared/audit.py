from app.shared.contracts import AuditEntry


class AuditLog:
    """Replace with a Neon-backed repository once persistence is introduced."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def for_incident(self, incident_id: str) -> list[AuditEntry]:
        return [entry for entry in self._entries if str(entry.incident_id) == incident_id]
