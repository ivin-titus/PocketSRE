from pathlib import Path

from app.config import get_settings
from app.storage.db import Database


def load_infra_context(docs_path: Path | None = None, db: Database | None = None) -> str:
    """Ground-truth context for LLM prompts: NeonDB docs first, `docs/infra/` fallback.

    DB docs are the confidential copy (uploaded via /api/knowledge/upload); the
    repo directory only holds sanitized, public-safe docs.
    """
    chunks: list[str] = ["=== MONITORED INFRASTRUCTURE TOPOLOGY & RUNBOOKS (GROUND TRUTH) ==="]

    if db is not None:
        try:
            for doc in db.list_knowledge_docs():
                chunks.append(f"\n--- [Document: {doc['doc_name']}] ---\n{doc['content'].strip()}\n")
        except Exception:
            pass  # DB offline: fall through to file docs

    target_path = docs_path or get_settings().infra_docs_path
    if target_path.is_dir():
        for file_path in sorted(target_path.glob("**/*")):
            if file_path.is_file() and file_path.suffix in (".md", ".txt"):
                try:
                    content = file_path.read_text(encoding="utf-8").strip()
                    chunks.append(f"\n--- [Document: {file_path.name}] ---\n{content}\n")
                except OSError:
                    continue

    chunks.append("=== END OF INFRASTRUCTURE GROUND TRUTH ===")
    return "\n".join(chunks) if len(chunks) > 2 else ""
