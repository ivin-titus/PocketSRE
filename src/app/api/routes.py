from datetime import UTC, datetime, timedelta
from hashlib import sha256
from hmac import compare_digest, new
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.actions.service import ActionService
from app.ai.knowledge import load_infra_context
from app.api.dependencies import actions, incidents
from app.config import get_settings
from app.incidents.service import IncidentService
from app.shared.contracts import ActionRequest, ActionResult, Incident, IncidentCreate, MagicLinkClaims

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/incidents", response_model=list[Incident])
def list_incidents(service: IncidentService = Depends(incidents)) -> list[Incident]:
    return service.list_all()


@router.post("/api/incidents", response_model=Incident, status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreate, service: IncidentService = Depends(incidents)) -> Incident:
    return service.create(payload)


@router.get("/api/incidents/{incident_id}", response_model=Incident)
def get_incident(incident_id: UUID, service: IncidentService = Depends(incidents)) -> Incident:
    incident = service.get(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.get("/api/infra/context")
def get_infra_context() -> dict[str, str]:
    return {"context": load_infra_context()}



@router.post("/api/actions/plan", response_model=ActionResult)
def plan_action(payload: ActionRequest, service: ActionService = Depends(actions)) -> ActionResult:
    try:
        return service.plan(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


def _signature(payload: str) -> str:
    return new(get_settings().magic_link_secret.encode(), payload.encode(), sha256).hexdigest()


@router.post("/api/incidents/{incident_id}/magic-link")
def create_magic_link(incident_id: UUID, request: Request, actor_id: str) -> dict[str, str]:
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    payload = f"{incident_id}:{actor_id}:{int(expires_at.timestamp())}"
    token = f"{payload}:{_signature(payload)}"
    return {"url": str(request.base_url).rstrip("/") + f"/console?token={token}"}


def parse_magic_link(token: str) -> MagicLinkClaims:
    try:
        incident_id, actor_id, timestamp, signature = token.rsplit(":", 3)
        payload = f"{incident_id}:{actor_id}:{timestamp}"
        expires_at = datetime.fromtimestamp(int(timestamp), tz=UTC)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid console link") from exc
    if not compare_digest(signature, _signature(payload)) or expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired or invalid console link")
    return MagicLinkClaims(incident_id=UUID(incident_id), actor_id=actor_id, expires_at=expires_at)
