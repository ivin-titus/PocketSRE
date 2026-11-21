"""LLM-assisted reactive triage: classify a human Discord message.

Falls back cleanly (returns None) on any provider failure — callers keep the
keyword heuristics as the deterministic path.
"""

import json

from app.ai.router import LLMRouter

_SERVICES = "yuki-core-api, yuki-discord-bot, yuki-telegram-bot, yuki-horiz-client, yuki-redis"

_PROMPT = """You are PocketSRE's triage parser for the Yuki infra
(services: {services}).

Classify this Discord message into strict JSON:
{{"intent": "status" | "incident" | "other",
 "service": one of the services or "unknown",
 "severity_hint": "P1" | "P2" | "P3" | "P4",
 "summary": "one-line operator-facing summary"}}

- "status" = asking whether systems are healthy.
- "incident" = reporting a concrete problem.
- "other" = anything unrelated; summary may be empty.
Message: {message}

{infra_context}"""


async def classify_message(
    router: LLMRouter | None,
    message: str,
    timeout: float = 20.0,
    infra_context: str = "",
) -> dict | None:
    """Return the parsed classification dict, or None if the LLM is unavailable."""
    if router is None or not message.strip():
        return None
    try:
        raw = await router.generate(
            _PROMPT.format(
                services=_SERVICES,
                message=message.strip(),
                infra_context=infra_context[:24_000],
            ),
            timeout_seconds=timeout,
        )
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        if data.get("intent") not in ("status", "incident", "other"):
            return None
        return data
    except Exception:
        return None
