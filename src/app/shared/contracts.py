from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class RunbookAction(str, Enum):
    FETCH_SERVICE_LOGS = "fetch_service_logs"
    RESTART_SERVICE = "restart_service"
    STOP_SERVICE = "stop_service"
    START_SERVICE = "start_service"
    INSPECT_SERVICE = "inspect_service"
    DOCKER_PS = "docker_ps"
    DOCKER_STATS = "docker_stats"
    DOCKER_TOP = "docker_top"
    DISK_PRUNE = "disk_prune"
    NGINX_RESTART = "nginx_restart"
    NGINX_STATUS = "nginx_status"
    NGINX_TEST = "nginx_test"
    SERVICE_JOURNAL = "service_journal"  # journalctl -u nginx|docker
    DOCKER_DAEMON_STATUS = "docker_daemon_status"


class ActorRole(str, Enum):
    VIEWER = "viewer"
    RESPONDER = "responder"
    LEAD = "lead"


class IncidentCreate(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    service: str = Field(min_length=1, max_length=128)
    summary: str = Field(min_length=1, max_length=2_000)
    severity: IncidentSeverity = IncidentSeverity.P2


class Incident(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source: str
    service: str
    summary: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActionParams(BaseModel):
    """Validated runbook parameters; never interpolated into shell text unsanitized."""

    tail_lines: int = Field(default=50, ge=1, le=500)
    grep: str | None = Field(default=None, max_length=128)
    freeform_command: str | None = Field(
        default=None,
        max_length=512,
        description="Ad-hoc bash (break-glass); EXECUTION_PRIVILEGE_MODE=full_root only",
    )


class ActionRequest(BaseModel):
    incident_id: UUID
    action: RunbookAction
    service: str = Field(min_length=1, max_length=128)
    actor_id: str = Field(min_length=1, max_length=128)
    actor_role: ActorRole
    approved: bool = False
    params: ActionParams = Field(default_factory=ActionParams)


class ActionResult(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    action: RunbookAction
    service: str
    status: str
    output: str = ""
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditEntry(BaseModel):
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    incident_id: UUID
    actor_id: str
    actor_role: ActorRole = ActorRole.VIEWER
    action: RunbookAction
    outcome: str


class MagicLinkClaims(BaseModel):
    incident_id: UUID
    actor_id: str
    expires_at: datetime
