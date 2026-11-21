from app.shared.contracts import RunbookAction


RUNBOOKS: dict[RunbookAction, dict[str, str]] = {
    RunbookAction.FETCH_SERVICE_LOGS: {
        "yuki-discord-bot": "sudo /usr/bin/docker logs --tail 50 yuki-discord-bot",
        "yuki-telegram-bot": "sudo /usr/bin/docker logs --tail 50 yuki-telegram-bot",
        "yuki-horiz-client": "sudo /usr/bin/docker logs --tail 50 yuki-horiz-client",
        "yuki-core-api": "sudo /usr/bin/docker logs --tail 50 yuki-core-api",
        "yuki-redis": "sudo /usr/bin/docker logs --tail 50 yuki-redis",
        # Backward compatibility aliases
        "yuki-core": "sudo /usr/bin/docker logs --tail 50 yuki-core-api",
        "horiz-connector": "sudo /usr/bin/docker logs --tail 50 yuki-horiz-client",
    },
    RunbookAction.RESTART_SERVICE: {
        "yuki-discord-bot": "sudo /usr/bin/docker restart yuki-discord-bot",
        "yuki-telegram-bot": "sudo /usr/bin/docker restart yuki-telegram-bot",
        "yuki-horiz-client": "sudo /usr/bin/docker restart yuki-horiz-client",
        "yuki-core-api": "sudo /usr/bin/docker restart yuki-core-api",
        "yuki-redis": "sudo /usr/bin/docker restart yuki-redis",
        # Backward compatibility aliases
        "yuki-core": "sudo /usr/bin/docker restart yuki-core-api",
        "horiz-connector": "sudo /usr/bin/docker restart yuki-horiz-client",
    },
    RunbookAction.STOP_SERVICE: {
        "yuki-discord-bot": "sudo /usr/bin/docker stop yuki-discord-bot",
        "yuki-telegram-bot": "sudo /usr/bin/docker stop yuki-telegram-bot",
        "yuki-horiz-client": "sudo /usr/bin/docker stop yuki-horiz-client",
        "yuki-core-api": "sudo /usr/bin/docker stop yuki-core-api",
        "yuki-redis": "sudo /usr/bin/docker stop yuki-redis",
    },
    RunbookAction.START_SERVICE: {
        "yuki-discord-bot": "sudo /usr/bin/docker start yuki-discord-bot",
        "yuki-telegram-bot": "sudo /usr/bin/docker start yuki-telegram-bot",
        "yuki-horiz-client": "sudo /usr/bin/docker start yuki-horiz-client",
        "yuki-core-api": "sudo /usr/bin/docker start yuki-core-api",
        "yuki-redis": "sudo /usr/bin/docker start yuki-redis",
    },
    RunbookAction.INSPECT_SERVICE: {
        "yuki-discord-bot": "sudo /usr/bin/docker inspect yuki-discord-bot",
        "yuki-telegram-bot": "sudo /usr/bin/docker inspect yuki-telegram-bot",
        "yuki-horiz-client": "sudo /usr/bin/docker inspect yuki-horiz-client",
        "yuki-core-api": "sudo /usr/bin/docker inspect yuki-core-api",
        "yuki-redis": "sudo /usr/bin/docker inspect yuki-redis",
    },
}


def command_for(action: RunbookAction, service: str) -> str:
    """Return only a declared command; caller input is never interpolated into shell text."""
    try:
        return RUNBOOKS[action][service]
    except KeyError as exc:
        raise ValueError(f"No runbook for {action.value} on {service}") from exc
