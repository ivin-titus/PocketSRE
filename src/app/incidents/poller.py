import asyncio
import json
import logging
from typing import Any
import urllib.request
from urllib.error import HTTPError, URLError

from app.actions.runbooks import resolve_container_name
from app.incidents.service import IncidentService
from app.shared.contracts import IncidentCreate, IncidentSeverity

logger = logging.getLogger(__name__)

ROUTE_CONTAINER_DEFAULTS: dict[str, str] = {
    "central": "yuki-core-api",
    "discord": "yuki-discord-bot",
    "horiz": "yuki-horiz-client",
    "telegram": "yuki-telegram-bot",
}


def _fetch_url_sync(url: str, timeout: float) -> tuple[int, str]:
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
    except URLError as exc:
        raise ConnectionError(f"Failed to connect to {url}: {exc.reason}") from exc


class PresencePoller:
    """Proactive background poller for target presence endpoints."""

    def __init__(
        self,
        base_url: str,
        endpoints: list[str],
        incidents: IncidentService,
        interval_seconds: float = 15.0,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints
        self.incidents = incidents
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self._running = False

    async def poll_endpoint(self, route: str) -> None:
        url = f"{self.base_url}/{route}"
        default_container = ROUTE_CONTAINER_DEFAULTS.get(route, "yuki-core-api")
        container = default_container

        try:
            status_code, body = await asyncio.to_thread(_fetch_url_sync, url, self.timeout_seconds)
        except Exception as exc:
            logger.warning("Presence poller connection error on %s: %s", url, exc)
            self._handle_failure(
                container=default_container,
                route=route,
                reason=f"Endpoint unreachable: {exc}",
                severity=IncidentSeverity.P1 if route == "central" else IncidentSeverity.P2,
            )
            return

        if status_code != 200:
            logger.warning("Presence poller non-200 HTTP %d on %s", status_code, url)
            self._handle_failure(
                container=default_container,
                route=route,
                reason=f"HTTP {status_code} returned by presence endpoint",
                severity=IncidentSeverity.P1 if route == "central" else IncidentSeverity.P2,
            )
            return

        try:
            data: dict[str, Any] = json.loads(body)
        except json.JSONDecodeError as exc:
            self._handle_failure(
                container=default_container,
                route=route,
                reason=f"Invalid JSON returned: {exc}",
                severity=IncidentSeverity.P2,
            )
            return

        # Resolve container name from payload or fallback
        raw_service = data.get("service") or default_container
        try:
            container = resolve_container_name(raw_service)
        except ValueError:
            container = default_container

        # Validate semantic health indicators
        failure_reasons = []

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

        if failure_reasons:
            severity = IncidentSeverity.P1 if (route == "central" or "db_status" in str(failure_reasons)) else IncidentSeverity.P2
            self._handle_failure(
                container=container,
                route=route,
                reason="; ".join(failure_reasons),
                severity=severity,
            )
        else:
            self._handle_recovery(container=container, route=route)

    def _handle_failure(self, container: str, route: str, reason: str, severity: IncidentSeverity) -> None:
        active = self.incidents.get_active_for_service(container)
        if not active:
            logger.info("Proactively raising incident for %s (%s): %s", container, route, reason)
            self.incidents.create(
                IncidentCreate(
                    source=f"presence_poller:{route}",
                    service=container,
                    summary=f"Proactive presence alert on {route}: {reason}",
                    severity=severity,
                )
            )

    def _handle_recovery(self, container: str, route: str) -> None:
        active = self.incidents.get_active_for_service(container)
        if active:
            logger.info("Service %s has recovered on %s. Resolving incident %s", container, route, active.id)
            self.incidents.resolve(active.id)

    async def poll_once(self) -> None:
        await asyncio.gather(*(self.poll_endpoint(route) for route in self.endpoints))

    async def run(self) -> None:
        self._running = True
        logger.info("PresencePoller started for %s with interval %ss", self.endpoints, self.interval_seconds)
        while self._running:
            try:
                await self.poll_once()
            except Exception as exc:
                logger.exception("Unexpected error during presence poll cycle: %s", exc)
            await asyncio.sleep(self.interval_seconds)

    def stop(self) -> None:
        self._running = False
