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
    RunbookAction.DOCKER_TOP: {
        container: f"sudo /usr/bin/docker top {container}"
        for container in AVAILABLE_CONTAINERS
    },
    # Host-level tools keyed to a single pseudo-service so command_for() stays uniform.
    RunbookAction.DOCKER_PS: {"host": "sudo /usr/bin/docker ps -a"},
    RunbookAction.DOCKER_STATS: {"host": "sudo /usr/bin/docker stats --no-stream"},
    RunbookAction.DISK_PRUNE: {"host": "sudo /usr/bin/docker system prune -f"},
    RunbookAction.NGINX_RESTART: {"host": "sudo /usr/bin/systemctl restart nginx"},
    RunbookAction.NGINX_STATUS: {"host": "sudo /usr/bin/systemctl status nginx"},
    RunbookAction.NGINX_TEST: {"host": "sudo /usr/bin/nginx -t"},
    RunbookAction.DOCKER_DAEMON_STATUS: {"host": "sudo /usr/bin/systemctl status docker"},
    RunbookAction.SERVICE_JOURNAL: {
        "nginx": "sudo /usr/bin/journalctl -u nginx -n 200 --no-pager",
        "docker": "sudo /usr/bin/journalctl -u docker -n 200 --no-pager",
    },
}

SERVICE_JOURNAL_UNITS: tuple[str, ...] = ("nginx", "docker")


def command_for(action: RunbookAction, service: str, params: ActionParams | None = None) -> str:
    """Return a declared command built from validated params only."""
    if action is RunbookAction.SERVICE_JOURNAL:
        if service not in SERVICE_JOURNAL_UNITS:
            raise ValueError(
                f"journal unit must be one of {SERVICE_JOURNAL_UNITS} (got '{service}')"
            )
        return RUNBOOKS[action][service]
    if action in {
        RunbookAction.DOCKER_PS,
        RunbookAction.DOCKER_STATS,
        RunbookAction.DISK_PRUNE,
        RunbookAction.NGINX_RESTART,
        RunbookAction.NGINX_STATUS,
        RunbookAction.NGINX_TEST,
        RunbookAction.DOCKER_DAEMON_STATUS,
    }:
        return RUNBOOKS[action]["host"]
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

