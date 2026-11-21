from pathlib import Path
from functools import lru_cache

from app.config import get_settings


def load_infra_context(docs_path: Path | None = None) -> str:
    """Read all markdown and text files in the infra docs directory for LLM grounding."""
    target_path = docs_path or get_settings().infra_docs_path
    if not target_path.is_dir():
        return ""

    chunks: list[str] = ["=== MONITORED INFRASTRUCTURE TOPOLOGY & RUNBOOKS (GROUND TRUTH) ==="]

    for file_path in sorted(target_path.glob("**/*")):
        if file_path.is_file() and file_path.suffix in (".md", ".txt"):
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                chunks.append(f"\n--- [Document: {file_path.name}] ---\n{content}\n")
            except OSError:
                continue

    chunks.append("=== END OF INFRASTRUCTURE GROUND TRUTH ===")
    return "\n".join(chunks)
