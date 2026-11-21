import asyncio
import json
import logging
from typing import Any

from app.actions.runbooks import resolve_container_name
from app.incidents.alerts import AlertBridge
from app.incidents.presence import ROUTE_CONTAINER_DEFAULTS, assess_health, fetch_url
from app.incidents.service import IncidentService
from app.shared.contracts import IncidentCreate, IncidentSeverity

logger = logging.getLogger(__name__)


class PresencePoller:
    """Proactive background poller for target presence endpoints."""

    def __init__(
        self,
        base_url: str,
        endpoints: list[str],
        incidents: IncidentService,
        interval_seconds: float = 15.0,
        timeout_seconds: float = 5.0,
        alerts: AlertBridge | None = None,
    ) -> None:
        self.alerts = alerts
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints
        self.incidents = incidents
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self._running = False
        self._fail_counts: dict[str, int] = {}  # consecutive-failure count per route
        self.flap_threshold = 2  # transient timeouts never open incidents

    async def poll_endpoint(self, route: str) -> None:
        url = f"{self.base_url}/{route}"
        default_container = ROUTE_CONTAINER_DEFAULTS.get(route, "yuki-core-api")
        container = default_container

        try:
            status_code, body = await asyncio.to_thread(fetch_url, url, self.timeout_seconds)
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

        failure_reasons = assess_health(route, data)
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
        self._fail_counts[route] = self._fail_counts.get(route, 0) + 1
        if self._fail_counts[route] < self.flap_threshold:
            logger.info("Transient failure on %s (%d/%d): %s", route, self._fail_counts[route], self.flap_threshold, reason)
            return
        active = self.incidents.get_active_for_service(container)
        if not active:
            logger.info("Proactively raising incident for %s (%s): %s", container, route, reason)
            incident = self.incidents.create(
                IncidentCreate(
                    source=f"presence_poller:{route}",
                    service=container,
                    summary=f"Proactive presence alert on {route}: {reason}",
                    severity=severity,
                )
            )
            if self.alerts:
                self.alerts.emit("opened", incident)

    def _handle_recovery(self, container: str, route: str) -> None:
        self._fail_counts.pop(route, None)
        active = self.incidents.get_active_for_service(container)
        # Only resolve incidents this poller opened — a healthy endpoint must never
        # close a webhook/reactive incident about a different issue on the same service.
        if active and active.source == f"presence_poller:{route}":
            resolved = self.incidents.resolve(active.id)
            if resolved and self.alerts:
                self.alerts.emit("resolved", resolved)

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
