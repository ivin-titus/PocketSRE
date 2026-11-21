from fastapi.testclient import TestClient

from app.main import app
from app.shared.magic_link import make_console_link
from app.config import get_settings


def _token_for(incident_id: str, actor_id: str = "lead-user") -> str:
    settings = get_settings()
    url = make_console_link("http://test", incident_id, actor_id, settings.magic_link_secret)
    return url.split("token=")[1]


def _create_incident(client: TestClient) -> str:
    res = client.post(
        "/api/incidents",
        json={
            "service": "yuki-core-api",
            "summary": "console test outage",
            "severity": "P1",
            "source": "presence_poller",
        },
    )
    return res.json()["id"]


def test_console_incident_requires_token() -> None:
    with TestClient(app) as client:
        res = client.get("/api/console/incident")
        assert res.status_code == 422
        res = client.get("/api/console/incident?token=bogus")
        assert res.status_code == 401


def test_console_incident_returns_detail_and_tools() -> None:
    with TestClient(app) as client:
        inc_id = _create_incident(client)
        token = _token_for(inc_id)
        res = client.get(f"/api/console/incident?token={token}")
        assert res.status_code == 200
        body = res.json()
        assert body["incident"]["service"] == "yuki-core-api"
        assert body["actor_id"] == "lead-user"
        assert any(t["mutating"] for t in body["tools"])
        assert any(t["name"] == "fetch_service_logs" for t in body["tools"])

        # Tool enrichment & categories
        tools_by_name = {t["name"]: t for t in body["tools"]}
        assert "label" in tools_by_name["fetch_service_logs"]
        assert tools_by_name["fetch_service_logs"]["category"] == "diagnostic"
        assert tools_by_name["fetch_service_logs"]["available"] is True

        # Availability filter for service_journal on yuki-core-api
        assert tools_by_name["service_journal"]["available"] is False
        assert "Journal is only supported" in tools_by_name["service_journal"]["unavailable_reason"]

        # Recommended action is present and safe
        assert "recommended_action" in body
        rec = body["recommended_action"]
        assert rec["mutating"] is False
        assert rec["action"] in ("fetch_service_logs", "inspect_service")


def test_console_action_rejects_unavailable_action() -> None:
    with TestClient(app) as client:
        inc_id = _create_incident(client)
        token = _token_for(inc_id)
        # service_journal is invalid for yuki-core-api
        res = client.post(f"/api/console/action?token={token}&action=service_journal")
        assert res.status_code == 422
        assert "Journal is only supported" in res.json()["detail"]


def test_console_action_rejects_unknown_tool() -> None:
    with TestClient(app) as client:
        inc_id = _create_incident(client)
        token = _token_for(inc_id)
        res = client.post(f"/api/console/action?token={token}&action=rm_rf")
        assert res.status_code == 422


def test_console_action_502_when_ssh_unconfigured() -> None:
    with TestClient(app) as client:
        inc_id = _create_incident(client)
        token = _token_for(inc_id)
        res = client.post(f"/api/console/action?token={token}&action=restart_service")
        assert res.status_code == 502  # executor exists? no — SSH not configured on test VM
        # 503 if executor is None; either way not 2xx — assert the envelope
        assert res.status_code in (502, 503)


def test_console_spend_and_health() -> None:
    with TestClient(app) as client:
        inc_id = _create_incident(client)
        token = _token_for(inc_id)
        spend = client.get(f"/api/console/spend?token={token}")
        assert spend.status_code == 200
        assert spend.json()["budgets"]["per_incident_usd"] == 5.0
        health = client.get(f"/api/console/health?token={token}")
        assert health.status_code == 200
        body = health.json()
        assert "cards" in body
        assert "summary" in body
        assert "overall_state" in body["summary"]
        assert "healthy_count" in body["summary"]
        assert "open_incidents" in body["summary"]
        for card in body["cards"].values():
            assert "state" in card
            assert "display_name" in card
            assert "reachable" in card
            assert "healthy" in card


def test_console_static_pages_served() -> None:
    with TestClient(app) as client:
        assert client.get("/console/").status_code == 200
        assert client.get("/console/mission-control.html").status_code == 200
        assert "PocketSRE" in client.get("/console/").text
