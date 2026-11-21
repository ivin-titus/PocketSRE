from app.shared.audit import AuditLog
from app.shared.contracts import ActionRequest, ActionResult, ActorRole, AuditEntry, RunbookAction

from .runbooks import command_for


class ActionService:
    def __init__(self, audit_log: AuditLog) -> None:
        self.audit_log = audit_log

    def validate(self, request: ActionRequest) -> str:
        command_for(request.action, request.service)
        if request.action in (RunbookAction.RESTART_SERVICE, RunbookAction.STOP_SERVICE, RunbookAction.START_SERVICE):
            if request.actor_role is not ActorRole.LEAD or not request.approved:
                raise PermissionError("Lifecycle actions require explicit approval from a lead.")
        return command_for(request.action, request.service)

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
                action=request.action,
                outcome=result.status,
            )
        )
        return result
