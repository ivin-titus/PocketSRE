from uuid import UUID

from app.shared.contracts import Incident, IncidentCreate, IncidentStatus


class IncidentService:
    """Small in-memory incident store; its interface is intentionally storage-agnostic."""

    def __init__(self) -> None:
        self._incidents: dict[UUID, Incident] = {}

    def create(self, payload: IncidentCreate) -> Incident:
        incident = Incident(**payload.model_dump())
        self._incidents[incident.id] = incident
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
        return incident

    def resolve(self, incident_id: UUID) -> Incident | None:
        incident = self.get(incident_id)
        if incident:
            incident.status = IncidentStatus.RESOLVED
        return incident

    def list_all(self) -> list[Incident]:
        return list(self._incidents.values())

