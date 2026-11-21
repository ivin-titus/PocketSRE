from app.actions.runbooks import command_for
from app.actions.tools import TOOL_REGISTRY, is_mutating, tool_schemas
from app.shared.contracts import ActionParams, RunbookAction


def test_fetch_logs_with_tail_and_grep_params() -> None:
    command = command_for(
        RunbookAction.FETCH_SERVICE_LOGS,
        "yuki-telegram-bot",
        ActionParams(tail_lines=200, grep="error|timeout"),
    )
    assert command == "sudo /usr/bin/docker logs --tail 200 yuki-telegram-bot | grep -iE 'error|timeout'"


def test_grep_pattern_is_shell_quoted() -> None:
    command = command_for(
        RunbookAction.FETCH_SERVICE_LOGS,
        "yuki-core-api",
        ActionParams(grep="weird (pattern)"),
    )
    assert "'weird (pattern)'" in command


def test_unsafe_grep_pattern_rejected() -> None:
    try:
        command_for(
            RunbookAction.FETCH_SERVICE_LOGS,
            "yuki-core-api",
            ActionParams(grep="x; rm -rf /"),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe grep pattern must be rejected")


def test_tail_lines_bounds() -> None:
    try:
        ActionParams(tail_lines=0)
    except Exception:
        pass
    else:
        raise AssertionError("tail_lines below 1 must fail validation")
    try:
        ActionParams(tail_lines=501)
    except Exception:
        pass
    else:
        raise AssertionError("tail_lines above 500 must fail validation")


def test_every_runbook_action_has_a_tool() -> None:
    actions = {spec.action for spec in TOOL_REGISTRY.values()}
    assert actions == set(RunbookAction)


def test_mutating_flags() -> None:
    assert is_mutating(RunbookAction.RESTART_SERVICE)
    assert is_mutating(RunbookAction.STOP_SERVICE)
    assert is_mutating(RunbookAction.START_SERVICE)
    assert not is_mutating(RunbookAction.FETCH_SERVICE_LOGS)
    assert not is_mutating(RunbookAction.INSPECT_SERVICE)


def test_tool_schemas_are_llm_ready() -> None:
    schemas = tool_schemas()
    assert len(schemas) == len(TOOL_REGISTRY)
    for schema in schemas:
        assert {"name", "description", "mutating", "parameters"} <= set(schema)
        assert "service" in schema["parameters"]["required"]
