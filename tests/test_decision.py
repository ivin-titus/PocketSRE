from unittest.mock import MagicMock, patch

from app.ai.decision import (
    AlertVerdict,
    GeminiDecisionClient,
    LocalDecisionClient,
    classify_alert,
    keyword_verdict,
)


def test_keyword_verdict_noise() -> None:
    v = keyword_verdict("chore: bump deps in yuki-core-api")
    assert not v.is_incident
    assert v.backend == "keywords"


def test_keyword_verdict_alert() -> None:
    v = keyword_verdict("yuki-core-api is DOWN — crash loop, restarting")
    assert v.is_incident
    assert v.service == "yuki-core-api"


def test_keyword_verdict_no_container() -> None:
    v = keyword_verdict("the service is having an error")
    assert not v.is_incident  # no named container


def test_gemini_decision_incident() -> None:
    answers = {
        "is_incident": MagicMock(noul=0.92, confidence=0.95),
        "service": MagicMock(choice="yuki-telegram-bot"),
    }
    result = MagicMock(answers=answers)
    with patch("google.genai.Client") as client_cls:
        client_cls.return_value.decisions.create.return_value = result
        v = GeminiDecisionClient("fake-key").classify("telegram bot crash")
    assert v.is_incident
    assert v.service == "yuki-telegram-bot"
    assert v.backend == "gemini_decision"


def test_gemini_decision_noise() -> None:
    answers = {
        "is_incident": MagicMock(noul=0.12, confidence=0.9),
        "service": MagicMock(choice="none"),
    }
    result = MagicMock(answers=answers)
    with patch("google.genai.Client") as client_cls:
        client_cls.return_value.decisions.create.return_value = result
        v = GeminiDecisionClient("fake-key").classify("pushed commit abc")
    assert not v.is_incident
    assert v.service is None


def test_classify_alert_fallback_on_failure() -> None:
    with patch.object(GeminiDecisionClient, "__init__", side_effect=RuntimeError("no network")):
        v = classify_alert(
            "yuki-core-api down",
            provider="gemini_decision",
            gemini_api_key="k",
        )
    assert v.backend == "keywords"  # degraded, not dropped


def test_classify_alert_provider_keywords() -> None:
    v = classify_alert("yuki-redis error", provider="keywords")
    assert v.is_incident and v.backend == "keywords"


def test_local_decision_client(monkeypatch) -> None:
    import io, json

    payload = json.dumps(
        {"is_incident": True, "service": "yuki-horiz-client", "confidence": 0.8}
    ).encode()

    class FakeResp:
        def read(self):
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: FakeResp())
    v = LocalDecisionClient("http://laya.internal").classify("horiz died")
    assert v.is_incident and v.service == "yuki-horiz-client" and v.backend == "local"
