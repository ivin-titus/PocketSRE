import json

from app.incidents.service import IncidentService
from app.shared.audit import AuditLog
from app.shared.contracts import (
    AuditEntry,
    IncidentCreate,
    IncidentSeverity,
    IncidentStatus,
    RunbookAction,
)


class FakeDatabase:
    def __init__(self) -> None:
        self.incidents: list[tuple] = []
        self.audits: list[tuple] = []
        self.spend: list[tuple] = []

    def upsert_incident(self, *args, resolved: bool = False) -> None:
        self.incidents.append((*args, resolved))

    def append_audit(self, *args) -> None:
        self.audits.append(args)

    def record_spend(self, *args) -> None:
        self.spend.append(args)


def _create() -> IncidentCreate:
    return IncidentCreate(
        service="yuki-core-api",
        summary="test outage",
        severity=IncidentSeverity.P1,
        source="presence_poller",
    )


def test_incident_writes_through_to_db() -> None:
    db = FakeDatabase()
    incidents = IncidentService(db=db)
    inc = incidents.create(_create())
    assert len(db.incidents) == 1
    assert db.incidents[0][1] == "yuki-core-api"
    assert db.incidents[0][2] == IncidentStatus.OPEN.value
    assert db.incidents[0][5] is False

    incidents.resolve(inc.id)
    assert db.incidents[-1][2] == IncidentStatus.RESOLVED.value
    assert db.incidents[-1][5] is True


def test_incident_service_without_db_stays_in_memory() -> None:
    incidents = IncidentService()
    inc = incidents.create(_create())
    assert incidents.get(inc.id) is inc


def test_audit_append_writes_db_and_jsonl(tmp_path) -> None:
    db = FakeDatabase()
    jsonl = tmp_path / "audit_log.jsonl"
    audit = AuditLog(db=db, jsonl_path=jsonl)
    incidents = IncidentService(db=db)
    inc = incidents.create(_create())

    audit.append(
        AuditEntry(
            incident_id=inc.id,
            actor_id="u1",
            action=RunbookAction.RESTART_SERVICE,
            outcome="verified",
        )
    )

    assert len(db.audits) == 1
    assert db.audits[0][3] == RunbookAction.RESTART_SERVICE.value
    line = json.loads(jsonl.read_text().strip())
    assert line["outcome"] == "verified"
    assert line["actor_id"] == "u1"
