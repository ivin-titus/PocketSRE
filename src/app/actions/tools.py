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


TOOL_REGISTRY: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in (
        ToolSpec(
            name="fetch_service_logs",
            action=RunbookAction.FETCH_SERVICE_LOGS,
            description="Fetch recent container logs. Params: tail_lines (1-500), grep (safe charset filter).",
            mutating=False,
        ),
        ToolSpec(
            name="inspect_container",
            action=RunbookAction.INSPECT_SERVICE,
            description="Show container state, restart count, exit code and config via docker inspect.",
            mutating=False,
        ),
        ToolSpec(
            name="restart_container",
            action=RunbookAction.RESTART_SERVICE,
            description="Restart a whitelisted Yuki container. Requires lead approval.",
            mutating=True,
        ),
        ToolSpec(
            name="stop_container",
            action=RunbookAction.STOP_SERVICE,
            description="Stop a whitelisted Yuki container. Requires lead approval.",
            mutating=True,
        ),
        ToolSpec(
            name="start_container",
            action=RunbookAction.START_SERVICE,
            description="Start a whitelisted Yuki container. Requires lead approval.",
            mutating=True,
        ),
        ToolSpec(
            name="docker_top",
            action=RunbookAction.DOCKER_TOP,
            description="List processes running inside a whitelisted container.",
            mutating=False,
        ),
        ToolSpec(
            name="docker_ps",
            action=RunbookAction.DOCKER_PS,
            description="List all containers and their status on the host.",
            mutating=False,
        ),
        ToolSpec(
            name="docker_stats",
            action=RunbookAction.DOCKER_STATS,
            description="One-shot CPU/mem/net I/O snapshot for all containers.",
            mutating=False,
        ),
        ToolSpec(
            name="disk_prune",
            action=RunbookAction.DISK_PRUNE,
            description="Prune dangling images/containers/volumes (docker system prune -f). Requires lead approval.",
            mutating=True,
        ),
        ToolSpec(
            name="nginx_restart",
            action=RunbookAction.NGINX_RESTART,
            description="Restart the host nginx ingress. Requires lead approval.",
            mutating=True,
        ),
        ToolSpec(
            name="nginx_status",
            action=RunbookAction.NGINX_STATUS,
            description="systemctl status nginx on the host.",
            mutating=False,
        ),
        ToolSpec(
            name="nginx_test",
            action=RunbookAction.NGINX_TEST,
            description="Validate nginx config (nginx -t) before any restart.",
            mutating=False,
        ),
        ToolSpec(
            name="service_journal",
            action=RunbookAction.SERVICE_JOURNAL,
            description="Last 200 systemd journal lines for the nginx or docker unit (service=nginx|docker).",
            mutating=False,
        ),
        ToolSpec(
            name="docker_daemon_status",
            action=RunbookAction.DOCKER_DAEMON_STATUS,
            description="systemctl status docker — daemon health on the host.",
            mutating=False,
        ),
    )
}


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
