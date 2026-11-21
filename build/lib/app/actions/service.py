import time

from app.incidents.presence import PresenceProbe
from app.shared.audit import AuditLog
from app.shared.contracts import ActionRequest, ActionResult, ActorRole, AuditEntry

from .runbooks import command_for
from .ssh_executor import SshExecutor, SshNotConfiguredError
from .tools import is_mutating


class ActionService:
    def __init__(
        self,
        audit_log: AuditLog,
        executor: SshExecutor | None = None,
        presence: PresenceProbe | None = None,
    ) -> None:
        self.audit_log = audit_log
        self.executor = executor
        self.presence = presence
        self._results: dict = {}

    def results_for(self, incident_id) -> list[ActionResult]:
        return list(self._results.get(incident_id, []))

    def validate(self, request: ActionRequest) -> str:
        if is_mutating(request.action):
            if request.actor_role is not ActorRole.LEAD or not request.approved:
                raise PermissionError("Lifecycle actions require explicit approval from a lead.")
        return command_for(request.action, request.service, request.params)

    def plan(self, request: ActionRequest) -> ActionResult:
        command = self.validate(request)
        result = ActionResult(
            incident_id=request.incident_id,
            action=request.action,
            service=request.service,
            status="approved_for_execution",
            output=command,
        )
        self.audit_log.append(
            AuditEntry(
                incident_id=request.incident_id,
                actor_id=request.actor_id,
                actor_role=request.actor_role,
                action=request.action,
                outcome=result.status,
            )
        )
        return result

    def _preflight(self, service: str) -> None:
        """Block mutations while the target reports maintenance_mode."""
        if self.presence is None:
            return
        reasons = self.presence.health_reasons(service)
        if reasons is None:
            return  # service has no presence coverage
        if any("maintenance_mode" in reason for reason in reasons):
            raise PermissionError(
                f"{service} is flagged maintenance_mode — mutating actions are blocked."
            )

    def _post_verify(self, service: str) -> str:
        """Re-check presence after a mutation; containers need a moment to come up."""
        if self.presence is None:
            return "executed_unverified"
        time.sleep(3)
        reasons = self.presence.health_reasons(service)
        if reasons is None:
            return "executed_unverified"  # no presence coverage (e.g. redis)
        if reasons:
            return f"executed_unverified ({'; '.join(reasons)})"
        return "verified"

    def execute(self, request: ActionRequest) -> ActionResult:
        """Validate, then actually run the whitelisted command on the target VM."""
        command = self.validate(request)
        if is_mutating(request.action):
            self._preflight(request.service)
        if self.executor is None:
            raise SshNotConfiguredError("SSH executor is not configured for this instance.")
        outcome = self.executor.run(command)
        output = outcome.stdout
        if outcome.stderr.strip():
            output += ("\n--- stderr ---\n" + outcome.stderr) if output else outcome.stderr
        status_text = "succeeded" if outcome.exit_code == 0 else f"failed (exit {outcome.exit_code})"
        if is_mutating(request.action) and outcome.exit_code == 0:
            status_text = self._post_verify(request.service)
        result = ActionResult(
            incident_id=request.incident_id,
            action=request.action,
            service=request.service,
            status=status_text,
            output=output[-20_000:],
        )
        self._results.setdefault(request.incident_id, []).append(result)
        self.audit_log.append(
            AuditEntry(
                incident_id=request.incident_id,
                actor_id=request.actor_id,
                actor_role=request.actor_role,
                action=request.action,
                outcome=result.status,
            )
        )
        return result
