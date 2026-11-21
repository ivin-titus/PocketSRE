"""Token-gated console API backing the /console pages.

All endpoints take the HMAC magic-link token as `?token=...`; the token encodes
incident_id + actor_id, and console actions run as that actor with LEAD role —
the magic link is only ever emitted on lead-facing cards.
"""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.actions.service import ActionService
from app.actions.tools import TOOL_REGISTRY
from app.api.dependencies import actions, incidents
from app.api.routes import parse_magic_link
from app.config import get_settings
from app.incidents.service import IncidentService
from app.shared.contracts import ActionParams, ActionRequest, RunbookAction

router = APIRouter(prefix="/api/console")


def claims(token: str) -> tuple[UUID, str]:
    c = parse_magic_link(token)
    return c.incident_id, c.actor_id


@router.get("/incident")
def console_incident(
    token: str = Query(...),
    service: IncidentService = Depends(incidents),
    action_service: ActionService = Depends(actions),
) -> dict:
    incident_id, actor_id = claims(token)
    incident = service.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    results = [r.model_dump(mode="json") for r in action_service.results_for(incident_id)]
    tools = [
        {"name": spec.name, "action": spec.action.value, "description": spec.description, "mutating": spec.mutating}
        for spec in TOOL_REGISTRY.values()
    ]
    return {
        "incident": incident.model_dump(mode="json"),
        "actor_id": actor_id,
        "action_results": results,
        "tools": tools,
    }


@router.post("/action")
def console_action(
    request: Request,
    token: str = Query(...),
    action: str = Query(...),
    tail_lines: int | None = Query(None),
    grep: str | None = Query(None),
    action_service: ActionService = Depends(actions),
) -> dict:
    """Execute a whitelisted runbook from the console. The click is the approval."""
    incident_id, actor_id = claims(token)
    try:
        runbook = RunbookAction(action)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Unknown action '{action}'") from exc
    incident_service: IncidentService = request.app.state.incidents
    incident = incident_service.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    params = ActionParams(tail_lines=tail_lines or 50, grep=grep)
    req = ActionRequest(
        incident_id=incident_id,
        action=runbook,
        service=incident.service,
        actor_id=actor_id,
        actor_role="lead",
        approved=True,
        params=params,
    )
    try:
        result = action_service.execute(req)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"result": result.model_dump(mode="json")}


@router.get("/health")
def console_health(request: Request, token: str = Query(...)) -> dict:
    claims(token)
    probe = request.app.state.probe
    presence_base = get_settings().presence_base_url
    endpoints = [e.strip() for e in get_settings().presence_endpoints.split(",") if e.strip()]
    cards = {}
    for ep in endpoints:
        try:
            payload = probe.payload_for(ep)
            reasons = probe.health_reasons(ep)
            cards[ep] = {
                "reachable": payload is not None,
                "healthy": reasons == [],
                "reasons": reasons or [],
                "payload": payload,
            }
        except Exception as exc:
            cards[ep] = {"reachable": False, "healthy": False, "reasons": [str(exc)], "payload": None}
    return {"presence_base": presence_base, "cards": cards}


@router.get("/spend")
def console_spend(request: Request, token: str = Query(...)) -> dict:
    incident_id, _ = claims(token)
    db = request.app.state.db
    total = db.incident_spend(incident_id) if db is not None else 0.0
    settings = get_settings()
    return {
        "incident_id": str(incident_id),
        "spent_usd": total,
        "budgets": {
            "per_incident_usd": settings.budget_per_incident_usd,
            "devin_usd": settings.budget_devin_usd,
            "llm_usd": settings.budget_llm_usd,
        },
        "db_connected": db is not None,
    }


@router.get("/stream")
async def console_stream(request: Request, token: str = Query(...)) -> StreamingResponse:
    claims(token)
    bridge = request.app.state.alerts

    async def events():
        yield "retry: 3000\n\n"
        while True:
            try:
                event = await asyncio.wait_for(bridge.next(), timeout=25.0)
                payload = {"kind": event.kind, "incident": event.incident.model_dump(mode="json")}
                yield f"data: {json.dumps(payload)}\n\n"
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
