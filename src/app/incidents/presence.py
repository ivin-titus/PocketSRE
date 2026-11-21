"""Shared presence checks used by both the poller and the action executor."""

import json
import urllib.request
from typing import Any
from urllib.error import HTTPError, URLError

from app.actions.runbooks import resolve_container_name

ROUTE_CONTAINER_DEFAULTS: dict[str, str] = {
    "central": "yuki-core-api",
    "discord": "yuki-discord-bot",
    "horiz": "yuki-horiz-client",
    "telegram": "yuki-telegram-bot",
}

CONTAINER_TO_ROUTE: dict[str, str] = {v: k for k, v in ROUTE_CONTAINER_DEFAULTS.items()}


def fetch_url(url: str, timeout: float) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PocketSRE-PresencePoller/1.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        return exc.code, body
    except Exception as exc:
        raise ConnectionError(f"Failed to connect to {url}: {exc}") from exc


def assess_health(route: str, data: dict[str, Any]) -> list[str]:
    """Return human-readable failure reasons for one presence payload; empty = healthy."""
    failure_reasons: list[str] = []

    if data.get("status") != "online":
        failure_reasons.append(f"status is '{data.get('status')}' (expected 'online')")

    if route == "central":
        if data.get("gate_mode") != "ACCEPTING":
            failure_reasons.append(f"gate_mode is '{data.get('gate_mode')}'")
        if data.get("db_status") != "ok":
            failure_reasons.append(f"db_status is '{data.get('db_status')}'")
        if data.get("redis_status") != "ok":
            failure_reasons.append(f"redis_status is '{data.get('redis_status')}'")

    flags = data.get("flags") or {}
    if flags.get("restart_recommended") is True:
        failure_reasons.append("restart_recommended flag is true")
    if flags.get("maintenance_mode") is True:
        failure_reasons.append("maintenance_mode flag is true")

    degraded = data.get("degraded_subsystems") or []
    if degraded:
        failure_reasons.append(f"degraded subsystems: {degraded}")

    platform_state = data.get("platform_connection_state")
    if platform_state and platform_state != "connected":
        failure_reasons.append(f"platform_connection_state is '{platform_state}'")

    return failure_reasons


class PresenceProbe:
    """Direct presence lookups for pre-flight and post-run verification."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def payload_for(self, service: str) -> tuple[str, dict[str, Any] | None]:
        """Fetch the presence payload for a service's route; (route, None) when unreachable."""
        if not self.base_url:
            return "", None
        if service in ROUTE_CONTAINER_DEFAULTS:
            route = service
        else:
            try:
                container = resolve_container_name(service)
            except ValueError:
                return "", None
            route = CONTAINER_TO_ROUTE.get(container)
            if not route:
                return "", None  # e.g. yuki-redis has no presence endpoint
        try:
            status_code, body = fetch_url(f"{self.base_url}/{route}", self.timeout_seconds)
        except ConnectionError:
            return route, None
        if status_code != 200:
            return route, None
        try:
            return route, json.loads(body)
        except json.JSONDecodeError:
            return route, None

    def health_reasons(self, service: str) -> list[str] | None:
        """Failure reasons for a service; None when the service has no presence coverage."""
        if not self.base_url:
            return None
        route, data = self.payload_for(service)
        if not route:
            return None
        if data is None:
            return ["presence endpoint unreachable or non-200"]
        return assess_health(route, data)
