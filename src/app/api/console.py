"""Token-gated console API backing the /console pages.

All endpoints take the HMAC magic-link token as `?token=...`; the token encodes
incident_id + actor_id, and console actions run as that actor with LEAD role —
the magic link is only ever emitted on lead-facing cards.
"""

import asyncio
import json
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.actions.runbooks import is_action_available
from app.actions.service import ActionService, EscalationRequiredError
from app.actions.tools import TOOL_REGISTRY, recommend_action
from app.api.dependencies import actions, incidents
from app.api.routes import parse_magic_link
from app.config import get_settings
from app.incidents.presence import assess_health
from app.incidents.service import IncidentService
from app.shared.budget import BudgetGovernor
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

    past_actions = [r.get("action", "") for r in results]
    rec_spec = recommend_action(incident.service, past_actions)

    tools = []
    for spec in TOOL_REGISTRY.values():
        available, unavailable_reason = is_action_available(spec.action, incident.service)
        tools.append(
            {
                "name": spec.name,
                "action": spec.action.value,
                "label": spec.label,
                "category": spec.category,
                "description": spec.description,
                "mutating": spec.mutating,
                "requires_approval": spec.requires_approval,
                "side_effect_warning": spec.side_effect_warning,
                "available": available,
                "unavailable_reason": unavailable_reason,
            }
        )

    recommended = {
        "name": rec_spec.name,
        "action": rec_spec.action.value,
        "label": rec_spec.label,
        "category": rec_spec.category,
        "description": rec_spec.description,
        "mutating": rec_spec.mutating,
        "requires_approval": rec_spec.requires_approval,
        "side_effect_warning": rec_spec.side_effect_warning,
    }

    return {
        "incident": incident.model_dump(mode="json"),
        "actor_id": actor_id,
        "action_results": results,
        "tools": tools,
        "recommended_action": recommended,
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

    available, reason = is_action_available(runbook, incident.service)
    if not available:
        raise HTTPException(
            status_code=422,
            detail=reason or f"Action '{action}' is not valid for target service '{incident.service}'",
        )

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
    except EscalationRequiredError as exc:
        raise HTTPException(
            status_code=409,
            detail={"reason": str(exc), "dossier": exc.dossier},
        ) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"result": result.model_dump(mode="json")}


@router.get("/health")
def console_health(request: Request, token: str = Query(...)) -> dict:
    claims(token)
    probe = getattr(request.app.state, "probe", None)
    settings = get_settings()
    presence_base = settings.presence_base_url
    endpoints = [e.strip() for e in settings.presence_endpoints.split(",") if e.strip()]
    cards = {}

    display_names = {
        "central": "Yuki Core (Central API)",
        "discord": "Yuki Discord Bot",
        "horiz": "Horiz Connector",
        "telegram": "Yuki Telegram Bot",
    }
    checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    healthy_count = 0
    degraded_count = 0
    unreachable_count = 0
    no_coverage_count = 0

    if not presence_base or not probe:
        for ep in endpoints:
            cards[ep] = {
                "display_name": display_names.get(ep, ep),
                "state": "not_configured",
                "reachable": False,
                "healthy": False,
                "reasons": ["Presence base URL or probe not configured"],
                "payload": None,
                "checked_at": checked_at,
            }
    else:
        for ep in endpoints:
            try:
                route, payload = probe.payload_for(ep)
                if not route:
                    cards[ep] = {
                        "display_name": display_names.get(ep, ep),
                        "state": "no_coverage",
                        "reachable": False,
                        "healthy": False,
                        "reasons": ["No presence coverage for service"],
                        "payload": None,
                        "checked_at": checked_at,
                    }
                    no_coverage_count += 1
                elif payload is None:
                    cards[ep] = {
                        "display_name": display_names.get(ep, ep),
                        "state": "unreachable",
                        "reachable": False,
                        "healthy": False,
                        "reasons": ["Presence endpoint unreachable or returned non-200 HTTP response"],
                        "payload": None,
                        "checked_at": checked_at,
                    }
                    unreachable_count += 1
                else:
                    reasons = assess_health(route, payload)
                    is_healthy = len(reasons) == 0
                    state = "healthy" if is_healthy else "degraded"
                    if is_healthy:
                        healthy_count += 1
                    else:
                        degraded_count += 1
                    cards[ep] = {
                        "display_name": display_names.get(ep, ep),
                        "state": state,
                        "reachable": True,
                        "healthy": is_healthy,
                        "reasons": reasons,
                        "payload": payload,
                        "checked_at": checked_at,
                    }
            except Exception as exc:
                cards[ep] = {
                    "display_name": display_names.get(ep, ep),
                    "state": "unreachable",
                    "reachable": False,
                    "healthy": False,
                    "reasons": [str(exc)],
                    "payload": None,
                    "checked_at": checked_at,
                }
                unreachable_count += 1

    if degraded_count > 0:
        overall_state = "degraded"
    elif unreachable_count > 0:
        overall_state = "unreachable"
    elif healthy_count > 0:
        overall_state = "healthy"
    else:
        overall_state = "unknown"

    incident_service: IncidentService | None = getattr(request.app.state, "incidents", None)
    open_incidents = (
        len([i for i in incident_service.list_all() if i.status.value in ("open", "triaged")])
        if incident_service
        else 0
    )

    summary = {
        "overall_state": overall_state,
        "healthy_count": healthy_count,
        "degraded_count": degraded_count,
        "unreachable_count": unreachable_count,
        "no_coverage_count": no_coverage_count,
        "open_incidents": open_incidents,
        "checked_at": checked_at,
    }

    return {"presence_base": presence_base, "summary": summary, "cards": cards}


@router.get("/spend")
def console_spend(request: Request, token: str = Query(...)) -> dict:
    incident_id, _ = claims(token)
    governor: BudgetGovernor | None = request.app.state.budget
    total = governor.incident_spend(incident_id) if governor else 0.0
    settings = get_settings()
    return {
        "incident_id": str(incident_id),
        "spent_usd": total,
        "provider_totals_usd": governor.provider_totals() if governor else {},
        "budgets": {
            "per_incident_usd": settings.budget_per_incident_usd,
            "devin_usd": settings.budget_devin_usd,
            "llm_usd": settings.budget_llm_usd,
            "sarvam_usd": settings.budget_sarvam_usd,
            "smallest_usd": settings.budget_smallest_usd,
        },
        "db_connected": request.app.state.db is not None,
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
