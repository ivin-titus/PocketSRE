import re
import shlex

from app.shared.contracts import ActionParams, RunbookAction

# grep patterns are applied in the remote shell pipeline, outside sudo. The charset
# whitelist keeps them readable while shlex.quote makes injection impossible.
_GREP_SAFE_PATTERN = re.compile(r"^[A-Za-z0-9 _.\-:|*+()\[\]^$]+$")


def _log_filter_suffix(grep: str | None) -> str:
    if not grep:
        return ""
    if not _GREP_SAFE_PATTERN.match(grep):
        raise ValueError(
            "grep pattern contains unsafe characters; allowed: letters, digits, space, _ . - : | * + ( ) [ ] ^ $"
        )
    return f" | grep -iE {shlex.quote(grep)}"

# All available target containers on the Project Yuki target VM
AVAILABLE_CONTAINERS: tuple[str, ...] = (
    "yuki-core-api",
    "yuki-horiz-client",
    "yuki-discord-bot",
    "yuki-telegram-bot",
    "yuki-redis",
)

# Service names exposed by presence endpoints or legacy aliases mapped to container names
SERVICE_TO_CONTAINER: dict[str, str] = {
    # Direct container names
    "yuki-core-api": "yuki-core-api",
    "yuki-horiz-client": "yuki-horiz-client",
    "yuki-discord-bot": "yuki-discord-bot",
    "yuki-telegram-bot": "yuki-telegram-bot",
    "yuki-redis": "yuki-redis",
    # Presence endpoint exposed names & backward-compatibility aliases
    "core-chat-api": "yuki-core-api",
    "yuki-core": "yuki-core-api",
    "horiz-connector": "yuki-horiz-client",
}


def resolve_container_name(service: str) -> str:
    """Normalize input service or alias into a verified target container name."""
    canonical = SERVICE_TO_CONTAINER.get(service)
    if canonical:
        return canonical
    raise ValueError(f"Unknown service or container: '{service}'. Available: {AVAILABLE_CONTAINERS}")


RUNBOOKS: dict[RunbookAction, dict[str, str]] = {
    RunbookAction.FETCH_SERVICE_LOGS: {
        container: f"sudo /usr/bin/docker logs {container}"
        for container in AVAILABLE_CONTAINERS
    },
    RunbookAction.RESTART_SERVICE: {
        container: f"sudo /usr/bin/docker restart {container}"
        for container in AVAILABLE_CONTAINERS
    },
    RunbookAction.STOP_SERVICE: {
        container: f"sudo /usr/bin/docker stop {container}"
        for container in AVAILABLE_CONTAINERS
    },
    RunbookAction.START_SERVICE: {
        container: f"sudo /usr/bin/docker start {container}"
        for container in AVAILABLE_CONTAINERS
    },
    RunbookAction.INSPECT_SERVICE: {
        container: f"sudo /usr/bin/docker inspect {container}"
        for container in AVAILABLE_CONTAINERS
    },
}


def command_for(action: RunbookAction, service: str, params: ActionParams | None = None) -> str:
    """Return a declared command built from validated params only."""
    container = resolve_container_name(service)
    try:
        command = RUNBOOKS[action][container]
    except KeyError as exc:
        raise ValueError(f"No runbook for {action.value} on container {container}") from exc
    if action is RunbookAction.FETCH_SERVICE_LOGS:
        params = params or ActionParams()
        command = f"sudo /usr/bin/docker logs --tail {params.tail_lines} {container}"
        command += _log_filter_suffix(params.grep)
    return command

