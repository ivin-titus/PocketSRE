from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.actions.service import ActionService
from app.actions.ssh_executor import CommandOutcome, SshNotConfiguredError
from app.shared.audit import AuditLog
from app.shared.contracts import ActionRequest, ActorRole, RunbookAction


class FakeExecutor:
    """Stands in for SshExecutor; records the command it was asked to run."""

    def __init__(self, outcome: CommandOutcome) -> None:
        self.outcome = outcome
        self.ran: list[str] = []

    def run(self, command: str) -> CommandOutcome:
        self.ran.append(command)
        return self.outcome


class FakeProbe:
    """Stands in for PresenceProbe; returns canned health reasons."""

    def __init__(self, reasons: list[str] | None) -> None:
        self.reasons = reasons

    def health_reasons(self, service: str) -> list[str] | None:
        return self.reasons


def _request(action: RunbookAction, role: ActorRole, approved: bool) -> ActionRequest:
    return ActionRequest(
        incident_id=uuid4(),
        action=action,
        service="yuki-telegram-bot",
        actor_id="discord-1",
        actor_role=role,
        approved=approved,
    )


def test_execute_runs_whitelisted_command_and_captures_streams() -> None:
    outcome = CommandOutcome(
        command="sudo /usr/bin/docker logs --tail 50 yuki-telegram-bot",
        exit_code=0,
        stdout="log-line-1\nlog-line-2",
        stderr="",
    )
    executor = FakeExecutor(outcome)
    service = ActionService(AuditLog(), executor)  # type: ignore[arg-type]

    result = service.execute(_request(RunbookAction.FETCH_SERVICE_LOGS, ActorRole.RESPONDER, approved=False))

    assert executor.ran == ["sudo /usr/bin/docker logs --tail 50 yuki-telegram-bot"]
    assert result.status == "succeeded"
    assert "log-line-1" in result.output


def test_execute_reports_nonzero_exit_code() -> None:
    executor = FakeExecutor(CommandOutcome(command="cmd", exit_code=1, stdout="", stderr="boom"))
    service = ActionService(AuditLog(), executor)  # type: ignore[arg-type]

    result = service.execute(_request(RunbookAction.FETCH_SERVICE_LOGS, ActorRole.RESPONDER, approved=False))

    assert result.status == "failed (exit 1)"
    assert "boom" in result.output


def test_execute_still_enforces_lead_approval_for_mutations() -> None:
    executor = FakeExecutor(CommandOutcome(command="cmd", exit_code=0, stdout="", stderr=""))
    service = ActionService(AuditLog(), executor)  # type: ignore[arg-type]

    try:
        service.execute(_request(RunbookAction.RESTART_SERVICE, ActorRole.RESPONDER, approved=True))
    except PermissionError:
        pass
    else:
        raise AssertionError("restart without lead role must be denied")

    assert executor.ran == []


def test_preflight_blocks_mutation_during_maintenance_mode() -> None:
    executor = FakeExecutor(CommandOutcome(command="cmd", exit_code=0, stdout="", stderr=""))
    probe = FakeProbe(["maintenance_mode flag is true"])
    service = ActionService(AuditLog(), executor, probe)  # type: ignore[arg-type]

    try:
        service.execute(_request(RunbookAction.RESTART_SERVICE, ActorRole.LEAD, approved=True))
    except PermissionError:
        pass
    else:
        raise AssertionError("mutation during maintenance_mode must be denied")

    assert executor.ran == []


def test_preflight_allows_mutation_when_healthy() -> None:
    executor = FakeExecutor(CommandOutcome(command="cmd", exit_code=0, stdout="restarted", stderr=""))
    probe = FakeProbe([])
    service = ActionService(AuditLog(), executor, probe)  # type: ignore[arg-type]

    result = service.execute(_request(RunbookAction.RESTART_SERVICE, ActorRole.LEAD, approved=True))

    assert executor.ran == ["sudo /usr/bin/docker restart yuki-telegram-bot"]
    assert result.status == "verified"


def test_post_verify_flags_service_still_unhealthy() -> None:
    executor = FakeExecutor(CommandOutcome(command="cmd", exit_code=0, stdout="restarted", stderr=""))
    probe = FakeProbe(["status is 'down' (expected 'online')"])
    service = ActionService(AuditLog(), executor, probe)  # type: ignore[arg-type]

    result = service.execute(_request(RunbookAction.RESTART_SERVICE, ActorRole.LEAD, approved=True))

    assert result.status.startswith("executed_unverified")
    assert "status is 'down'" in result.status


def test_execute_requires_configured_executor() -> None:
    service = ActionService(AuditLog())

    try:
        service.execute(_request(RunbookAction.FETCH_SERVICE_LOGS, ActorRole.RESPONDER, approved=False))
    except SshNotConfiguredError:
        pass
    else:
        raise AssertionError("unconfigured executor must raise SshNotConfiguredError")


def test_from_settings_rejects_missing_host(tmp_path) -> None:
    from app.config import Settings
    from app.actions.ssh_executor import SshExecutor

    settings = Settings(target_ssh_host=None, target_ssh_key_path=tmp_path / "key")
    try:
        SshExecutor.from_settings(settings)
    except SshNotConfiguredError:
        pass
    else:
        raise AssertionError("missing host must raise SshNotConfiguredError")


def test_from_settings_rejects_missing_key(tmp_path) -> None:
    from app.config import Settings
    from app.actions.ssh_executor import SshExecutor

    settings = Settings(target_ssh_host="203.0.113.10", target_ssh_key_path=tmp_path / "nope")
    try:
        SshExecutor.from_settings(settings)
    except SshNotConfiguredError:
        pass
    else:
        raise AssertionError("missing key must raise SshNotConfiguredError")


def test_run_wraps_connect_failures(tmp_path) -> None:
    import paramiko
    from app.actions.ssh_executor import SshExecutionError, SshExecutor

    key_path = tmp_path / "key"
    key_path.write_text("fake")
    executor = SshExecutor(host="203.0.113.10", user="pocketsre", key_path=key_path)

    with patch.object(paramiko.Ed25519Key, "from_private_key_file", return_value=MagicMock()):
        with patch.object(paramiko.SSHClient, "connect", side_effect=paramiko.SSHException("nope")):
            try:
                executor.run("sudo /usr/bin/docker ps")
            except SshExecutionError:
                pass
            else:
                raise AssertionError("connect failure must raise SshExecutionError")
