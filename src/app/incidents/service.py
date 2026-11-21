from uuid import UUID

from app.shared.contracts import Incident, IncidentCreate, IncidentStatus
from app.storage.db import Database


class IncidentService:
    """Incident store: in-memory primary, Neon write-through when configured."""

    def __init__(self, db: Database | None = None) -> None:
        self._incidents: dict[UUID, Incident] = {}
        self._db = db

    def _persist(self, incident: Incident) -> None:
        if self._db is None:
            return
        self._db.upsert_incident(
            incident.id,
            incident.service,
            incident.status.value,
            incident.severity.value,
            incident.summary,
            resolved=incident.status is IncidentStatus.RESOLVED,
        )

    def create(self, payload: IncidentCreate) -> Incident:
        incident = Incident(**payload.model_dump())
        self._incidents[incident.id] = incident
        self._persist(incident)
        return incident

    def get(self, incident_id: UUID) -> Incident | None:
        return self._incidents.get(incident_id)

    def get_active_for_service(self, service: str) -> Incident | None:
        """Find an active (OPEN or TRIAGED) incident for the given service."""
        for inc in reversed(list(self._incidents.values())):
            if inc.service == service and inc.status in (IncidentStatus.OPEN, IncidentStatus.TRIAGED):
                return inc
        return None

    def triage(self, incident_id: UUID) -> Incident | None:
        incident = self.get(incident_id)
        if incident:
            incident.status = IncidentStatus.TRIAGED
            self._persist(incident)
        return incident

    def resolve(self, incident_id: UUID) -> Incident | None:
        incident = self.get(incident_id)
        if incident:
            incident.status = IncidentStatus.RESOLVED
            self._persist(incident)
        return incident

    def list_all(self) -> list[Incident]:
        return list(self._incidents.values())

