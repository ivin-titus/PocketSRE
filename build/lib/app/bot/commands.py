"""Discord adapter entry points.

The bot will call incident/action services directly in this process. Platform APIs
must not contain incident policy or shell-command construction.
"""

from app.incidents.service import IncidentService
from app.shared.contracts import IncidentCreate, IncidentSeverity


def create_text_incident(incidents: IncidentService, service: str, summary: str):
    return incidents.create(
        IncidentCreate(source="discord", service=service, summary=summary, severity=IncidentSeverity.P2)
    )
