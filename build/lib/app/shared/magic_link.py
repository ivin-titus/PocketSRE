from datetime import UTC, datetime, timedelta
from hashlib import sha256
from hmac import new
from uuid import UUID


def signature(payload: str, secret: str) -> str:
    return new(secret.encode(), payload.encode(), sha256).hexdigest()


def make_console_link(
    base_url: str,
    incident_id: UUID,
    actor_id: str,
    secret: str,
    ttl_minutes: int = 15,
) -> str:
    """Build a signed 15-minute console link. Token format: id:actor:exp_ts:sig."""
    expires_at = datetime.now(UTC) + timedelta(minutes=ttl_minutes)
    payload = f"{incident_id}:{actor_id}:{int(expires_at.timestamp())}"
    token = f"{payload}:{signature(payload, secret)}"
    return f"{base_url.rstrip('/')}/console?token={token}"
