from pathlib import Path
from app.ai.knowledge import load_infra_context


def test_load_infra_context_reads_yuki_architecture() -> None:
    context = load_infra_context(Path("docs/infra"))
    assert "MONITORED INFRASTRUCTURE TOPOLOGY & RUNBOOKS" in context
    assert "yuki-core-api" in context
    assert "yuki-discord-bot" in context
    assert "yuki-redis" in context
    assert "https://yuki-net.ivin.site" in context
