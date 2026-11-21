"""Alert-vs-noise decision classifier.

Primary backend: Gemini Decision 1 (`gemini-decision-1`) via the Decisions API —
purpose-built binary/categorical verdicts with zero output tokens (free tier
200 RPM / 10K RPD). A pluggable `local` provider targets a small decision model
endpoint (e.g. Laya or an Ollama-hosted model) via `DECISION_BASE_URL` for
air-gapped deployments. Any backend failure falls back to keyword heuristics so
detection never hard-depends on a model being reachable.
"""

import json
import logging
import urllib.request
from dataclasses import dataclass

logger = logging.getLogger(__name__)

KNOWN_CONTAINERS = (
    "yuki-core-api",
    "yuki-discord-bot",
    "yuki-telegram-bot",
    "yuki-horiz-client",
    "yuki-redis",
)

_KEYWORDS = ("crash", "down", "error", "alert", "incident", "oom", "500", "unhealthy", "restart", "failed", "offline")


@dataclass
class AlertVerdict:
    is_incident: bool
    service: str | None
    confidence: float
    backend: str  # "gemini_decision" | "local" | "keywords"


def keyword_verdict(content: str) -> AlertVerdict:
    lowered = content.lower()
    named = [c for c in KNOWN_CONTAINERS if c in lowered or c.replace("yuki-", "") in lowered]
    is_incident = bool(named) and any(k in lowered for k in _KEYWORDS)
    return AlertVerdict(
        is_incident=is_incident,
        service=named[0] if named else None,
        confidence=0.0,
        backend="keywords",
    )


class GeminiDecisionClient:
    """Gemini Decision 1 via the google-genai Decisions API (v1beta)."""

    def __init__(self, api_key: str, model: str = "gemini-decision-1") -> None:
        from google import genai  # lazy — only needed when this backend is selected

        self._client = genai.Client(
            api_key=api_key, http_options={"api_version": "v1beta"}
        )
        self._model = model

    def classify(self, content: str) -> AlertVerdict:
        result = self._client.decisions.create(
            model=self._model,
            input=content[:4000],
            questions={
                "is_incident": {
                    "type": "noul",
                    "instructions": (
                        "Does this message describe a real infrastructure or service "
                        "incident needing SRE attention (crash, outage, error storm, "
                        "OOM, unhealthy service)? False for routine chatter, commits, "
                        "CI notifications, announcements, or informational posts."
                    ),
                },
                "service": {
                    "type": "choice",
                    "instructions": "Which Yuki service does this incident concern?",
                    "criteria": {
                        **{c: f"Messages about the {c} container/service." for c in KNOWN_CONTAINERS},
                        "none": "No specific Yuki service identifiable.",
                    },
                },
            },
        )
        answers = result.answers
        incident_answer = answers["is_incident"]
        service_answer = answers["service"]
        service = getattr(service_answer, "choice", "none")
        return AlertVerdict(
            is_incident=getattr(incident_answer, "noul", 0.0) >= 0.5,
            service=service if service in KNOWN_CONTAINERS else None,
            confidence=float(getattr(incident_answer, "confidence", 0.0) or 0.0),
            backend="gemini_decision",
        )


class LocalDecisionClient:
    """Local decision model (Laya / Ollama-class) over DECISION_BASE_URL.

    Expects POST {base}/classify with {"content": str} returning
    {"is_incident": bool, "service": str|null, "confidence": float}.
    """

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._url = f"{base_url.rstrip('/')}/classify"
        self._timeout = timeout

    def classify(self, content: str) -> AlertVerdict:
        req = urllib.request.Request(
            self._url,
            data=json.dumps({"content": content[:4000]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            payload = json.loads(resp.read().decode())
        service = payload.get("service")
        return AlertVerdict(
            is_incident=bool(payload.get("is_incident")),
            service=service if service in KNOWN_CONTAINERS else None,
            confidence=float(payload.get("confidence") or 0.0),
            backend="local",
        )


def classify_alert(
    content: str,
    *,
    provider: str,
    gemini_api_key: str | None = None,
    decision_model: str = "gemini-decision-1",
    local_base_url: str | None = None,
) -> AlertVerdict:
    """Decision-model verdict with deterministic keyword fallback."""
    try:
        if provider == "gemini_decision" and gemini_api_key:
            return GeminiDecisionClient(gemini_api_key, model=decision_model).classify(content)
        if provider == "local" and local_base_url:
            return LocalDecisionClient(local_base_url).classify(content)
    except Exception as exc:  # never let a model outage blind detection
        logger.warning("Decision backend %s failed (%r) — falling back to keywords", provider, exc)
    return keyword_verdict(content)
