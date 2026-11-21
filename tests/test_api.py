from fastapi.testclient import TestClient

from app.main import app
from app.ai.key_pool import KeyPool
import asyncio


def test_health() -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_restart_requires_lead_approval() -> None:
    with TestClient(app) as client:
        incident = client.post(
            "/api/incidents",
            json={"source": "test", "service": "yuki-core-api", "summary": "Container unavailable"},
        ).json()
        response = client.post(
            "/api/actions/plan",
            json={
                "incident_id": incident["id"],
                "action": "restart_service",
                "service": "yuki-core-api",
                "actor_id": "discord-1",
                "actor_role": "responder",
                "approved": False,
            },
        )
    assert response.status_code == 403


def test_fetch_logs_is_a_declared_runbook() -> None:
    with TestClient(app) as client:
        incident = client.post(
            "/api/incidents",
            json={"source": "test", "service": "yuki-core-api", "summary": "Container unavailable"},
        ).json()
        response = client.post(
            "/api/actions/plan",
            json={
                "incident_id": incident["id"],
                "action": "fetch_service_logs",
                "service": "yuki-core-api",
                "actor_id": "discord-1",
                "actor_role": "responder",
            },
        )
    assert response.status_code == 200
    assert response.json()["output"] == "sudo /usr/bin/docker logs --tail 50 yuki-core-api"



def test_key_pool_cools_a_failed_key_and_uses_the_other_key() -> None:
    async def scenario() -> tuple[str, str]:
        pool = KeyPool(["key-one", "key-two"])
        first = await pool.acquire()
        await pool.record_failure(first, retry_after=60)
        return first, await pool.acquire()

    first, second = asyncio.run(scenario())
    assert first != second
