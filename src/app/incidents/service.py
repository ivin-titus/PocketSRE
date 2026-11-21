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

    def triage(self, incident_id: UUID) -> Incident | None:
        incident = self.get(incident_id)
        if incident:
            incident.status = IncidentStatus.TRIAGED
        return incident
