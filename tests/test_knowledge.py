from fastapi.testclient import TestClient

from app.ai.knowledge import load_infra_context
from app.config import get_settings
from app.main import app


class FakeKnowledgeDb:
    def __init__(self) -> None:
        self.docs: dict[str, str] = {}

    def upsert_knowledge_doc(self, doc_name: str, content: str) -> None:
        self.docs[doc_name] = content

    def list_knowledge_docs(self) -> list[dict]:
        return [
            {"doc_name": k, "content": v, "uploaded_at": "2026-01-01T00:00:00+00:00"}
            for k, v in sorted(self.docs.items())
        ]


def test_context_db_docs_first() -> None:
    db = FakeKnowledgeDb()
    db.upsert_knowledge_doc("secret-infra.md", "real host details here")
    ctx = load_infra_context(docs_path=None, db=db)
    assert "secret-infra.md" in ctx
    assert "real host details here" in ctx


def test_context_files_when_no_db(tmp_path) -> None:
    (tmp_path / "public.md").write_text("sanitized doc")
    ctx = load_infra_context(docs_path=tmp_path, db=None)
    assert "sanitized doc" in ctx


def test_context_empty_when_nothing(tmp_path) -> None:
    assert load_infra_context(docs_path=tmp_path, db=None) == ""


def test_upload_requires_admin_secret() -> None:
    with TestClient(app) as client:
        res = client.post("/api/knowledge/upload", files={"file": ("a.md", b"x")})
        assert res.status_code == 401


def test_upload_and_list_flow() -> None:
    secret = get_settings().magic_link_secret
    db = FakeKnowledgeDb()
    with TestClient(app) as client:
        app.state.db = db
        res = client.post(
            "/api/knowledge/upload",
            headers={"x-admin-secret": secret},
            files={"file": ("infra.md", b"confidential topology")},
        )
        assert res.status_code == 200
        assert res.json()["doc_name"] == "infra.md"
        assert db.docs["infra.md"] == "confidential topology"

        listing = client.get("/api/knowledge", headers={"x-admin-secret": secret})
        assert listing.status_code == 200
        assert listing.json()["docs"][0]["doc_name"] == "infra.md"

        ctx = client.get("/api/infra/context")
        assert "confidential topology" in ctx.json()["context"]


def test_upload_rejects_non_doc_suffix() -> None:
    secret = get_settings().magic_link_secret
    with TestClient(app) as client:
        app.state.db = FakeKnowledgeDb()
        res = client.post(
            "/api/knowledge/upload",
            headers={"x-admin-secret": secret},
            files={"file": ("evil.py", b"print(1)")},
        )
        assert res.status_code == 422
