import asyncio
import json
from unittest.mock import patch

from app.incidents.poller import PresencePoller
from app.incidents.service import IncidentService
from app.shared.contracts import IncidentStatus, IncidentSeverity


def test_poller_healthy_endpoint_creates_no_incident() -> None:
    service = IncidentService()
    poller = PresencePoller(
        base_url="https://yuki-net.ivin.site/presence",
        endpoints=["central"],
        incidents=service,
    )

    healthy_payload = {
        "status": "online",
        "gate_mode": "ACCEPTING",
        "db_status": "ok",
        "redis_status": "ok",
        "service": "core-chat-api",
        "flags": {"restart_recommended": False, "maintenance_mode": False},
        "degraded_subsystems": [],
    }

    with patch("app.incidents.poller.fetch_url", return_value=(200, json.dumps(healthy_payload))):
        asyncio.run(poller.poll_endpoint("central"))

    assert len(service.list_all()) == 0


def test_poller_degraded_creates_incident_and_maps_container() -> None:
    service = IncidentService()
    poller = PresencePoller(
        base_url="https://yuki-net.ivin.site/presence",
        endpoints=["central"],
        incidents=service,
    )

    degraded_payload = {
        "status": "degraded",
        "gate_mode": "ACCEPTING",
        "db_status": "error",
        "redis_status": "ok",
        "service": "core-chat-api",
        "flags": {"restart_recommended": True},
        "degraded_subsystems": ["database"],
    }

    with patch("app.incidents.poller.fetch_url", return_value=(200, json.dumps(degraded_payload))):
        asyncio.run(poller.poll_endpoint("central"))
        asyncio.run(poller.poll_endpoint("central"))  # threshold=2: second consecutive failure opens it

    incidents = service.list_all()
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.service == "yuki-core-api"
    assert inc.status == IncidentStatus.OPEN
    assert inc.severity == IncidentSeverity.P1
    assert "db_status" in inc.summary

    # Second poll should deduplicate and not create a second incident
    with patch("app.incidents.poller.fetch_url", return_value=(200, json.dumps(degraded_payload))):
        asyncio.run(poller.poll_endpoint("central"))

    assert len(service.list_all()) == 1

    # Recovery poll should resolve the active incident
    recovered_payload = {
        "status": "online",
        "gate_mode": "ACCEPTING",
        "db_status": "ok",
        "redis_status": "ok",
        "service": "core-chat-api",
        "flags": {"restart_recommended": False},
        "degraded_subsystems": [],
    }
    with patch("app.incidents.poller.fetch_url", return_value=(200, json.dumps(recovered_payload))):
        asyncio.run(poller.poll_endpoint("central"))

    assert len(service.list_all()) == 1
    assert service.get(inc.id).status == IncidentStatus.RESOLVED


def test_poller_edge_client_disconnection() -> None:
    service = IncidentService()
    poller = PresencePoller(
        base_url="https://yuki-net.ivin.site/presence",
        endpoints=["discord"],
        incidents=service,
    )

    disconnected_payload = {
        "status": "online",
        "service": "yuki-discord-bot",
        "platform_connection_state": "disconnected",
        "flags": {"restart_recommended": False},
        "degraded_subsystems": [],
    }

    with patch("app.incidents.poller.fetch_url", return_value=(200, json.dumps(disconnected_payload))):
        asyncio.run(poller.poll_endpoint("discord"))
        asyncio.run(poller.poll_endpoint("discord"))

    incidents = service.list_all()
    assert len(incidents) == 1
    assert incidents[0].service == "yuki-discord-bot"
    assert "platform_connection_state" in incidents[0].summary


def test_poller_flap_threshold() -> None:
    import asyncio, json
    from unittest.mock import patch
    from app.incidents.service import IncidentService
    from app.shared.contracts import IncidentStatus

    svc = IncidentService()
    poller = PresencePoller(base_url="http://x", endpoints=["central"], incidents=svc)
    bad = {"status": "offline"}
    with patch("app.incidents.poller.fetch_url", return_value=(200, json.dumps(bad))):
        asyncio.run(poller.poll_endpoint("central"))
        assert len(svc.list_all()) == 0  # single flap → no incident
        asyncio.run(poller.poll_endpoint("central"))
        assert len(svc.list_all()) == 1  # second consecutive → incident


def test_poller_does_not_resolve_foreign_incidents() -> None:
    import asyncio, json
    from unittest.mock import patch
    from app.incidents.service import IncidentService
    from app.shared.contracts import IncidentCreate, IncidentSeverity

    svc = IncidentService()
    svc.create(IncidentCreate(source="discord_webhook", service="yuki-core-api",
                            summary="webhook crash", severity=IncidentSeverity.P1))
    poller = PresencePoller(base_url="http://x", endpoints=["central"], incidents=svc)
    good = {"status": "online", "gate_mode": "ACCEPTING", "db_status": "ok", "redis_status": "ok"}
    with patch("app.incidents.poller.fetch_url", return_value=(200, json.dumps(good))):
        asyncio.run(poller.poll_endpoint("central"))
    assert svc.list_all()[0].status.value == "open"  # untouched: not opened by this poller
