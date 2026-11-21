import asyncio
import json
from unittest.mock import patch

from app.bot.discord_runtime import actor_role_for, truncate
from app.incidents.alerts import AlertBridge
from app.incidents.poller import PresencePoller
from app.incidents.service import IncidentService
from app.shared.contracts import ActorRole, IncidentStatus


def test_actor_role_mapping() -> None:
    assert actor_role_for(["SRE-Lead", "everyone"]) is ActorRole.LEAD
    assert actor_role_for(["DevOps"]) is ActorRole.RESPONDER
    assert actor_role_for(["random"]) is ActorRole.VIEWER
    assert actor_role_for([]) is ActorRole.VIEWER


def test_truncate() -> None:
    assert truncate("short") == "short"
    assert len(truncate("x" * 2000)) == 1000
    assert truncate("x" * 2000).endswith("...")


def test_poller_emits_opened_and_resolved_events() -> None:
    service = IncidentService()
    bridge = AlertBridge()
    poller = PresencePoller(
        base_url="https://yuki-net.ivin.site/presence",
        endpoints=["central"],
        incidents=service,
        alerts=bridge,
    )

    degraded_payload = {
        "status": "degraded",
        "service": "core-chat-api",
        "flags": {"restart_recommended": True},
        "degraded_subsystems": ["database"],
    }
    healthy_payload = {
        "status": "online",
        "gate_mode": "ACCEPTING",
        "db_status": "ok",
        "redis_status": "ok",
        "service": "core-chat-api",
        "flags": {"restart_recommended": False, "maintenance_mode": False},
        "degraded_subsystems": [],
    }

    async def scenario() -> list[str]:
        with patch(
            "app.incidents.poller.fetch_url", return_value=(200, json.dumps(degraded_payload))
        ):
            await poller.poll_endpoint("central")
        opened = await asyncio.wait_for(bridge.next(), timeout=1)

        with patch(
            "app.incidents.poller.fetch_url", return_value=(200, json.dumps(healthy_payload))
        ):
            await poller.poll_endpoint("central")
        resolved = await asyncio.wait_for(bridge.next(), timeout=1)
        return [opened.kind, resolved.kind, resolved.incident.status.value]

    kinds = asyncio.run(scenario())
    assert kinds == ["opened", "resolved", "resolved"]
    assert service.list_all()[0].status == IncidentStatus.RESOLVED
