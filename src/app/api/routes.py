from datetime import UTC, datetime
from hmac import compare_digest
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.actions.service import ActionService
from app.actions.ssh_executor import SshExecutionError, SshNotConfiguredError
from app.ai.knowledge import load_infra_context
from app.api.dependencies import actions, incidents
from app.config import get_settings
from app.incidents.service import IncidentService
from app.shared.contracts import ActionRequest, ActionResult, Incident, IncidentCreate, MagicLinkClaims
from app.shared.magic_link import make_console_link, signature as _sign

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
def get_infra_context(request: Request) -> dict[str, str]:
    return {"context": load_infra_context(db=request.app.state.db)}


@router.post("/api/knowledge/upload")
async def upload_knowledge_doc(request: Request) -> dict:
    """Upload an infra doc into `infra_knowledge_docs`. Operator-only: the
    `x-admin-secret` header must match the magic-link secret."""
    settings = get_settings()
    secret = request.headers.get("x-admin-secret", "")
    if not settings.magic_link_secret or not compare_digest(secret, settings.magic_link_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret")
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="NeonDB not configured")
    form = await request.form()
    file = form.get("file")
    if file is None or not getattr(file, "filename", ""):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="file field required")
    name = Path(file.filename).name
    if Path(name).suffix.lower() not in (".md", ".txt"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only .md/.txt docs accepted")
    content = (await file.read()).decode("utf-8", errors="replace")
    if len(content) > 256_000:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Doc too large (256KB max)")
    db.upsert_knowledge_doc(name, content)
    return {"doc_name": name, "bytes": len(content)}


@router.get("/api/knowledge")
def list_knowledge_docs(request: Request) -> dict:
    secret = request.headers.get("x-admin-secret", "")
    settings = get_settings()
    if not settings.magic_link_secret or not compare_digest(secret, settings.magic_link_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret")
    db = request.app.state.db
    if db is None:
        return {"docs": []}
    return {"docs": [{"doc_name": d["doc_name"], "uploaded_at": d["uploaded_at"]} for d in db.list_knowledge_docs()]}



@router.post("/api/actions/plan", response_model=ActionResult)
def plan_action(payload: ActionRequest, service: ActionService = Depends(actions)) -> ActionResult:
    try:
        return service.plan(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/api/actions/execute", response_model=ActionResult)
def execute_action(payload: ActionRequest, service: ActionService = Depends(actions)) -> ActionResult:
    """Validate and run a whitelisted runbook on the target VM over SSH."""
    try:
        return service.execute(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SshNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except SshExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/api/incidents/{incident_id}/magic-link")
def create_magic_link(incident_id: UUID, request: Request, actor_id: str) -> dict[str, str]:
    url = make_console_link(
        str(request.base_url), incident_id, actor_id, get_settings().magic_link_secret
    )
    return {"url": url}


def parse_magic_link(token: str) -> MagicLinkClaims:
    try:
        incident_id, actor_id, timestamp, signature = token.rsplit(":", 3)
        payload = f"{incident_id}:{actor_id}:{timestamp}"
        expires_at = datetime.fromtimestamp(int(timestamp), tz=UTC)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid console link") from exc
    if not compare_digest(signature, _sign(payload, get_settings().magic_link_secret)) or expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired or invalid console link")
    return MagicLinkClaims(incident_id=UUID(incident_id), actor_id=actor_id, expires_at=expires_at)
