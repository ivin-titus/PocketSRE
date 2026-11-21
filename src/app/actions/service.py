import time

from app.incidents.presence import PresenceProbe
from app.shared.audit import AuditLog
from app.shared.contracts import ActionRequest, ActionResult, ActorRole, AuditEntry

from .runbooks import command_for
from .ssh_executor import SshExecutor, SshNotConfiguredError
from .tools import is_mutating


class EscalationRequiredError(Exception):
    """Raised when an incident exhausts its autonomy budget (max trials / repeat attempt).
    Carries a 4-pillar dossier for the break-glass hand-off."""

    def __init__(self, reason: str, dossier: dict) -> None:
        super().__init__(reason)
        self.dossier = dossier


class ActionService:
    def __init__(
        self,
        audit_log: AuditLog,
        executor: SshExecutor | None = None,
        presence: PresenceProbe | None = None,
        max_trials: int = 3,
        privilege_mode: str = "non_root",
    ) -> None:
        self.audit_log = audit_log
        self.executor = executor
        self.presence = presence
        self.max_trials = max_trials
        self.privilege_mode = privilege_mode
        self._results: dict = {}

    def results_for(self, incident_id) -> list[ActionResult]:
        return list(self._results.get(incident_id, []))

    def validate(self, request: ActionRequest) -> str:
        if is_mutating(request.action):
            if request.actor_role is not ActorRole.LEAD or not request.approved:
                raise PermissionError("Lifecycle actions require explicit approval from a lead.")
        if request.params and request.params.freeform_command:
            # FULL_ROOT break-glass: ad-hoc bash, still lead-gated + audited.
            if self.privilege_mode != "full_root":
                raise PermissionError(
                    "freeform commands require EXECUTION_PRIVILEGE_MODE=full_root "
                    "(whitelist-only under non_root)."
                )
            return request.params.freeform_command
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

    def _loop_guard(self, request: ActionRequest) -> None:
        """Anti-loop: cap mutating trials per incident; never re-run an already-tried mutation."""
        prior = [r for r in self._results.get(request.incident_id, []) if is_mutating(r.action)]
        halt: str | None = None
        if any(r.action == request.action for r in prior):
            halt = "repeat attempt blocked"
        elif len(prior) >= self.max_trials:
            halt = "max trials reached"
        if halt:
            self.audit_log.append(
                AuditEntry(
                    incident_id=request.incident_id,
                    actor_id=request.actor_id,
                    actor_role=request.actor_role,
                    action=request.action,
                    outcome="escalated",
                )
            )
            raise EscalationRequiredError(
                (
                    f"{request.action.value} already attempted — escalating instead of looping."
                    if halt == "repeat attempt blocked"
                    else f"Incident exhausted its autonomy budget ({self.max_trials} mutating trials) — escalating to lead."
                ),
                self.escalation_dossier(request.incident_id, halt),
            )

    def escalation_dossier(self, incident_id, halt_reason: str) -> dict:
        """4-pillar analyst dossier: happened / tried / halted / next steps."""
        results = self.results_for(incident_id)
        mutating = [r for r in results if is_mutating(r.action)]
        health = (
            self.presence.health_reasons(results[-1].service)
            if self.presence is not None and results
            else None
        )
        return {
            "what_happened": (
                results[0].status if results else "incident opened; no action run yet"
            ),
            "what_was_tried": [
                {"action": r.action.value, "status": r.status} for r in results
            ],
            "why_halted": halt_reason,
            "trials_used": len(mutating),
            "max_trials": self.max_trials,
            "current_health": health or ["presence coverage unavailable"],
            "next_steps": [
                "Inspect live logs via the console log tail.",
                "Run an ad-hoc diagnostic from the break-glass console.",
                "Dispatch Devin if the failure is a code regression.",
                "SSH in as the lead and resolve manually if the fault is outside the whitelist.",
            ],
        }

    def execute(self, request: ActionRequest) -> ActionResult:
        """Validate, then actually run the whitelisted command on the target VM."""
        command = self.validate(request)
        if is_mutating(request.action):
            self._loop_guard(request)
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
