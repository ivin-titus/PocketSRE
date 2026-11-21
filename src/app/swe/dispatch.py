"""Devin dispatch for code-regression incidents (PRD §4.6)."""

import json
import urllib.request
from urllib.error import HTTPError, URLError

from app.shared.contracts import Incident


class DevinDispatcher:
    """Creates a Devin session for an incident; deterministic stub without a key."""

    def __init__(self, api_key: str | None, timeout_seconds: float = 15.0) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def dispatch(self, incident: Incident) -> str:
        """Return the Devin session URL, or a stub note when unconfigured."""
        if not self.api_key:
            return (
                "⚠️ `DEVIN_API_KEY` not configured — escalate manually: "
                f"incident `{incident.id}` on `{incident.service}`."
            )
        prompt = (
            f"Investigate and fix a {incident.severity.value} incident on Yuki container "
            f"`{incident.service}`.\n\nSummary: {incident.summary}\n\n"
            "Check recent container logs and code, open a fix PR if the root cause is in code."
        )
        req = urllib.request.Request(
            "https://api.devin.ai/v1/sessions",
            data=json.dumps({"prompt": prompt}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return f"⚠️ Devin dispatch failed: HTTP {exc.code}"
        except URLError as exc:
            return f"⚠️ Devin dispatch failed: {exc.reason}"
        url = data.get("url") or f"https://app.devin.ai/sessions/{data.get('session_id', '')}"
        return f"🤖 Devin session dispatched: {url}"
