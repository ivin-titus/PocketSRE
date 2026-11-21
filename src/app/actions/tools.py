from dataclasses import dataclass

from app.shared.contracts import RunbookAction


@dataclass(frozen=True)
class ToolSpec:
    """One typed tool the agent may call. Commands come from runbooks.command_for();

    the agent picks a tool and supplies params — it never writes raw CLI text.
    """

    name: str
    action: RunbookAction
    description: str
    mutating: bool
    label: str = ""
    category: str = "diagnostic"  # "diagnostic" | "recovery" | "advanced"
    requires_approval: bool = False
    side_effect_warning: str | None = None


TOOL_REGISTRY: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in (
        ToolSpec(
            name="fetch_service_logs",
            action=RunbookAction.FETCH_SERVICE_LOGS,
            label="Fetch latest logs",
            category="diagnostic",
            description="Fetch recent container logs. Params: tail_lines (1-500), grep (safe charset filter).",
            mutating=False,
            requires_approval=False,
        ),
        ToolSpec(
            name="inspect_container",
            action=RunbookAction.INSPECT_SERVICE,
            label="Inspect container",
            category="diagnostic",
            description="Show container state, restart count, exit code and config via docker inspect.",
            mutating=False,
            requires_approval=False,
        ),
        ToolSpec(
            name="docker_top",
            action=RunbookAction.DOCKER_TOP,
            label="Container processes (top)",
            category="diagnostic",
            description="List processes running inside a whitelisted container.",
            mutating=False,
            requires_approval=False,
        ),
        ToolSpec(
            name="restart_container",
            action=RunbookAction.RESTART_SERVICE,
            label="Restart container",
            category="recovery",
            description="Restart a whitelisted Yuki container. Requires lead approval.",
            mutating=True,
            requires_approval=True,
            side_effect_warning="Container will restart, temporarily dropping active connections and in-flight requests.",
        ),
        ToolSpec(
            name="stop_container",
            action=RunbookAction.STOP_SERVICE,
            label="Stop container",
            category="recovery",
            description="Stop a whitelisted Yuki container. Requires lead approval.",
            mutating=True,
            requires_approval=True,
            side_effect_warning="Container will halt immediately and cease serving traffic until restarted.",
        ),
        ToolSpec(
            name="start_container",
            action=RunbookAction.START_SERVICE,
            label="Start container",
            category="recovery",
            description="Start a whitelisted Yuki container. Requires lead approval.",
            mutating=True,
            requires_approval=True,
            side_effect_warning="Starts an existing stopped container instance.",
        ),
        ToolSpec(
            name="docker_ps",
            action=RunbookAction.DOCKER_PS,
            label="List host containers (ps)",
            category="advanced",
            description="List all containers and their status on the host.",
            mutating=False,
            requires_approval=False,
        ),
        ToolSpec(
            name="docker_stats",
            action=RunbookAction.DOCKER_STATS,
            label="Host resource stats (stats)",
            category="advanced",
            description="One-shot CPU/mem/net I/O snapshot for all containers.",
            mutating=False,
            requires_approval=False,
        ),
        ToolSpec(
            name="disk_prune",
            action=RunbookAction.DISK_PRUNE,
            label="Prune docker resources (prune)",
            category="advanced",
            description="Prune dangling images/containers/volumes (docker system prune -f). Requires lead approval.",
            mutating=True,
            requires_approval=True,
            side_effect_warning="Permanently removes stopped containers, unused networks, and dangling image layers.",
        ),
        ToolSpec(
            name="nginx_restart",
            action=RunbookAction.NGINX_RESTART,
            label="Restart nginx ingress",
            category="advanced",
            description="Restart the host nginx ingress. Requires lead approval.",
            mutating=True,
            requires_approval=True,
            side_effect_warning="Nginx process will restart on the host, briefly interrupting reverse proxy ingress.",
        ),
        ToolSpec(
            name="nginx_status",
            action=RunbookAction.NGINX_STATUS,
            label="Check nginx status",
            category="advanced",
            description="systemctl status nginx on the host.",
            mutating=False,
            requires_approval=False,
        ),
        ToolSpec(
            name="nginx_test",
            action=RunbookAction.NGINX_TEST,
            label="Test nginx config (nginx -t)",
            category="advanced",
            description="Validate nginx config (nginx -t) before any restart.",
            mutating=False,
            requires_approval=False,
        ),
        ToolSpec(
            name="service_journal",
            action=RunbookAction.SERVICE_JOURNAL,
            label="View systemd journal",
            category="advanced",
            description="Last 200 systemd journal lines for the nginx or docker unit (service=nginx|docker).",
            mutating=False,
            requires_approval=False,
        ),
        ToolSpec(
            name="docker_daemon_status",
            action=RunbookAction.DOCKER_DAEMON_STATUS,
            label="Check docker daemon status",
            category="advanced",
            description="systemctl status docker — daemon health on the host.",
            mutating=False,
            requires_approval=False,
        ),
    )
}


def recommend_action(service: str, past_actions: list[str]) -> ToolSpec:
    """Recommend the most helpful safe next action for an on-call SRE.

    Never defaults to a destructive action. Prefers logs first, then container inspection.
    """
    past_actions_set = set(past_actions)
    if "fetch_service_logs" not in past_actions_set and RunbookAction.FETCH_SERVICE_LOGS.value not in past_actions_set:
        return spec_for(RunbookAction.FETCH_SERVICE_LOGS)
    if "inspect_container" not in past_actions_set and RunbookAction.INSPECT_SERVICE.value not in past_actions_set:
        return spec_for(RunbookAction.INSPECT_SERVICE)
    return spec_for(RunbookAction.FETCH_SERVICE_LOGS)


def spec_for(action: RunbookAction) -> ToolSpec:
    return next(s for s in TOOL_REGISTRY.values() if s.action is action)


def is_mutating(action: RunbookAction) -> bool:
    return spec_for(action).mutating


def tool_schemas() -> list[dict[str, object]]:
    """JSON-schema-ish tool descriptions for the LLM router (Phase 1 free-text input)."""
    params_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Service or container name"},
            "tail_lines": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
            "grep": {
                "type": "string",
                "maxLength": 128,
                "description": "Optional log filter (safe charset only)",
            },
        },
        "required": ["service"],
    }
    return [
        {"name": s.name, "description": s.description, "mutating": s.mutating, "parameters": params_schema}
        for s in TOOL_REGISTRY.values()
    ]
