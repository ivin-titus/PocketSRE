"""Configurable Discord-role → ActorRole mapping (PRD ROLE_PERMISSIONS)."""

from app.shared.contracts import ActorRole

_ROLE_RANK = {ActorRole.VIEWER: 0, ActorRole.RESPONDER: 1, ActorRole.LEAD: 2}

DEFAULT_ROLE_PERMISSIONS: dict[str, ActorRole] = {
    "SRE-Lead": ActorRole.LEAD,
    "DevOps": ActorRole.RESPONDER,
    "Junior-Dev": ActorRole.VIEWER,
}


def parse_role_permissions(raw: str) -> dict[str, ActorRole]:
    """Parse 'SRE-Lead:lead,DevOps:responder,Junior-Dev:viewer' into a map."""
    mapping: dict[str, ActorRole] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        name, _, level = pair.partition(":")
        try:
            mapping[name.strip()] = ActorRole(level.strip().lower())
        except ValueError as exc:
            raise ValueError(
                f"Invalid role permission '{pair}'; level must be lead|responder|viewer"
            ) from exc
    return mapping or dict(DEFAULT_ROLE_PERMISSIONS)


def actor_role_for(
    role_names: list[str], permissions: dict[str, ActorRole] | None = None
) -> ActorRole:
    """Highest-ranked ActorRole the member's Discord roles grant."""
    mapping = permissions or DEFAULT_ROLE_PERMISSIONS
    best = ActorRole.VIEWER
    for name in role_names:
        granted = mapping.get(name)
        if granted is not None and _ROLE_RANK[granted] > _ROLE_RANK[best]:
            best = granted
    return best
