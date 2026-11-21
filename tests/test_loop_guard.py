from uuid import uuid4

import pytest

from app.actions.service import ActionService, EscalationRequiredError
from app.actions.ssh_executor import CommandOutcome
from app.shared.audit import AuditLog
from app.shared.contracts import ActionRequest, ActorRole, RunbookAction


class FakeExecutor:
    def run(self, command: str) -> CommandOutcome:
        return CommandOutcome(command=command, exit_code=0, stdout="ok", stderr="")


class FakeProbe:
    def health_reasons(self, service: str) -> list[str] | None:
        return None  # no presence coverage → post-verify lands executed_unverified


def _req(incident_id, action: RunbookAction) -> ActionRequest:
    return ActionRequest(
        incident_id=incident_id,
        action=action,
        service="yuki-telegram-bot",
        actor_id="lead-1",
        actor_role=ActorRole.LEAD,
        approved=True,
    )


def _service(max_trials: int = 3) -> ActionService:
    return ActionService(AuditLog(), executor=FakeExecutor(), presence=FakeProbe(), max_trials=max_trials)


def test_repeat_mutation_escalates() -> None:
    svc = _service()
    inc = uuid4()
    svc.execute(_req(inc, RunbookAction.RESTART_SERVICE))
    with pytest.raises(EscalationRequiredError) as exc:
        svc.execute(_req(inc, RunbookAction.RESTART_SERVICE))
    assert "already attempted" in str(exc.value)
    assert exc.value.dossier["why_halted"] == "repeat attempt blocked"
    assert exc.value.dossier["trials_used"] == 1


def test_max_trials_escalates() -> None:
    svc = _service(max_trials=2)
    inc = uuid4()
    svc.execute(_req(inc, RunbookAction.RESTART_SERVICE))
    svc.execute(_req(inc, RunbookAction.STOP_SERVICE))
    with pytest.raises(EscalationRequiredError) as exc:
        svc.execute(_req(inc, RunbookAction.START_SERVICE))
    assert "autonomy budget" in str(exc.value)
    dossier = exc.value.dossier
    assert dossier["why_halted"] == "max trials reached"
    assert dossier["trials_used"] == 2
    assert dossier["max_trials"] == 2
    assert len(dossier["what_was_tried"]) == 2
    assert dossier["next_steps"]


def test_diagnostics_do_not_count_toward_trials() -> None:
    svc = _service(max_trials=1)
    inc = uuid4()
    svc.execute(_req(inc, RunbookAction.FETCH_SERVICE_LOGS))
    svc.execute(_req(inc, RunbookAction.INSPECT_SERVICE))
    result = svc.execute(_req(inc, RunbookAction.RESTART_SERVICE))
    assert result.status == "executed_unverified"


def test_escalation_audited() -> None:
    audit = AuditLog()
    svc = ActionService(audit, executor=FakeExecutor(), presence=FakeProbe(), max_trials=1)
    inc = uuid4()
    svc.execute(_req(inc, RunbookAction.RESTART_SERVICE))
    with pytest.raises(EscalationRequiredError):
        svc.execute(_req(inc, RunbookAction.STOP_SERVICE))
    assert audit.for_incident(str(inc))[-1].outcome == "escalated"
