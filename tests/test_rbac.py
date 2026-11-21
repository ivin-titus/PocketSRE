from app.shared.contracts import ActorRole
from app.shared.rbac import DEFAULT_ROLE_PERMISSIONS, actor_role_for, parse_role_permissions


def test_default_map() -> None:
    assert DEFAULT_ROLE_PERMISSIONS["SRE-Lead"] is ActorRole.LEAD
    assert DEFAULT_ROLE_PERMISSIONS["DevOps"] is ActorRole.RESPONDER
    assert DEFAULT_ROLE_PERMISSIONS["Junior-Dev"] is ActorRole.VIEWER


def test_actor_role_defaults_to_viewer() -> None:
    assert actor_role_for(["random-role"]) is ActorRole.VIEWER
    assert actor_role_for([]) is ActorRole.VIEWER  # DM members expose no roles


def test_highest_rank_wins() -> None:
    assert actor_role_for(["Junior-Dev", "SRE-Lead"]) is ActorRole.LEAD
    assert actor_role_for(["Junior-Dev", "DevOps"]) is ActorRole.RESPONDER


def test_parse_role_permissions_custom_map() -> None:
    mapping = parse_role_permissions("Ops:lead,Dev:responder")
    assert mapping == {"Ops": ActorRole.LEAD, "Dev": ActorRole.RESPONDER}
    assert actor_role_for(["Ops"], mapping) is ActorRole.LEAD
    assert actor_role_for(["SRE-Lead"], mapping) is ActorRole.VIEWER


def test_parse_role_permissions_invalid_level() -> None:
    try:
        parse_role_permissions("Ops:superadmin")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown permission level must raise ValueError")


def test_parse_role_permissions_empty_falls_back() -> None:
    assert parse_role_permissions("  ") == DEFAULT_ROLE_PERMISSIONS
