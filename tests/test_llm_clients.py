import asyncio
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.factory import build_llm_router
from app.ai.key_pool import KeyPool
from app.ai.router import LLMRouter
from app.ai.triage import classify_message, is_status_query
from app.config import Settings


def run(coro):
    return asyncio.run(coro)


# ---- Gemini provider ----

class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


def _gemini_provider():
    fake_genai = ModuleType("google.genai")
    fake_types = ModuleType("google.genai.types")
    fake_errors = ModuleType("google.genai.errors")

    class APIError(Exception):
        pass

    class ClientError(APIError):
        pass

    class ServerError(APIError):
        pass

    class GenerateContentConfig:
        def __init__(self, **kw):
            self.kw = kw

    class FakeModels:
        def generate_content(self, **kwargs):
            return _FakeResponse("ok: all good")

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.models = FakeModels()

    fake_genai.Client = FakeClient
    fake_types.GenerateContentConfig = GenerateContentConfig
    fake_errors.APIError = APIError
    fake_errors.ClientError = ClientError
    fake_errors.ServerError = ServerError

    with patch.dict(
        sys.modules,
        {
            "google": ModuleType("google"),
            "google.genai": fake_genai,
            "google.genai.types": fake_types,
            "google.genai.errors": fake_errors,
        },
    ):
        import importlib

        import app.ai.clients.gemini as g
        import app.ai.clients.openai as o

        importlib.reload(g)
        importlib.reload(o)  # rebinds LLMAPIError/LLMRateLimitError to the reloaded classes
        return g.GeminiProvider(), g


def test_gemini_generate_success() -> None:
    provider, _mod = _gemini_provider()
    out = run(provider.generate(api_key="k", model="m", prompt="ping", timeout_seconds=5.0))
    assert out == "ok: all good"


def test_gemini_rate_limit_normalized() -> None:
    provider, mod = _gemini_provider()
    with patch.object(
        provider, "_call_sync", side_effect=mod.LLMRateLimitError("x")
    ):
        with pytest.raises(mod.LLMRateLimitError):
            run(provider.generate(api_key="k", model="m", prompt="p", timeout_seconds=5.0))


# ---- OpenAI provider ----

def test_openai_generate_success() -> None:
    from app.ai.clients.openai import OpenAIProvider

    fake_choice = MagicMock()
    fake_choice.finish_reason = "stop"
    fake_choice.message.content = "pong"
    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        return_value=MagicMock(choices=[fake_choice])
    )
    with patch("app.ai.clients.openai.openai.AsyncOpenAI", return_value=fake_client):
        provider = OpenAIProvider()
        out = run(provider.generate(api_key="k", model="m", prompt="ping", timeout_seconds=5.0))
        assert out == "pong"


def test_openai_empty_response_raises() -> None:
    from app.ai.clients.openai import OpenAIProvider
    from app.ai.clients.gemini import LLMAPIError

    fake_choice = MagicMock()
    fake_choice.finish_reason = "stop"
    fake_choice.message.content = "  "
    fake_choice.message.refusal = None
    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        return_value=MagicMock(choices=[fake_choice])
    )
    with patch("app.ai.clients.openai.openai.AsyncOpenAI", return_value=fake_client):
        with pytest.raises(LLMAPIError):
            run(OpenAIProvider().generate(api_key="k", model="m", prompt="ping", timeout_seconds=5.0))


def test_openai_rate_limit_normalized() -> None:
    import openai as oai
    from app.ai.clients.gemini import LLMRateLimitError
    from app.ai.clients.openai import OpenAIProvider

    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        side_effect=oai.RateLimitError("rl", response=MagicMock(status_code=429), body=None)
    )
    with patch("app.ai.clients.openai.openai.AsyncOpenAI", return_value=fake_client):
        with pytest.raises(LLMRateLimitError):
            run(OpenAIProvider().generate(api_key="k", model="m", prompt="ping", timeout_seconds=5.0))


# ---- factory ----

def test_factory_none_without_keys() -> None:
    s = Settings(gemini_api_keys="", ai_provider="gemini")
    assert build_llm_router(s) is None


def test_factory_gemini_router() -> None:
    s = Settings(gemini_api_keys="k1,k2", ai_provider="gemini")
    router = build_llm_router(s)
    assert router is not None and router.model == s.gemini_model


def test_factory_openai_router() -> None:
    s = Settings(ai_provider="openai", openai_api_key="sk-x", openai_model="m")
    router = build_llm_router(s)
    assert router is not None and router.model == "m"


def test_factory_unknown_provider() -> None:
    s = Settings(ai_provider="weird")
    assert build_llm_router(s) is None


# ---- triage ----

def test_classify_message_no_router() -> None:
    assert run(classify_message(None, "is everything fine?")) is None


def test_classify_message_parses_json() -> None:
    class FakeProvider:
        async def generate(self, **kw):
            return '{"intent": "incident", "service": "yuki-core-api", "severity_hint": "P1", "summary": "api down"}'

    router = LLMRouter(FakeProvider(), KeyPool(["k"]), "m")
    out = run(classify_message(router, "prod api is down!!"))
    assert out["intent"] == "incident"
    assert out["severity_hint"] == "P1"
    assert out["response_language"] == "english"


def test_classify_message_falls_back_to_detected_manglish_language() -> None:
    class FakeProvider:
        async def generate(self, **kw):
            return '{"intent": "incident", "service": "yuki-core-api", "severity_hint": "P2", "summary": "issue"}'

    router = LLMRouter(FakeProvider(), KeyPool(["k"]), "m")
    out = run(classify_message(router, "core api down aayi, onnu nokk"))
    assert out["response_language"] == "manglish"


def test_manglish_status_query_is_deterministically_recognized() -> None:
    assert is_status_query("Yuki de services ellam okay aano?")


def test_classify_message_bad_json_returns_none() -> None:
    class FakeProvider:
        async def generate(self, **kw):
            return "not json"

    router = LLMRouter(FakeProvider(), KeyPool(["k"]), "m")
    assert run(classify_message(router, "hello")) is None


def test_classify_message_strips_code_fence() -> None:
    class FakeProvider:
        async def generate(self, **kw):
            return '```json\n{"intent": "status", "service": "yuki-core-api", "severity_hint": "P4", "summary": "check"}\n```'

    router = LLMRouter(FakeProvider(), KeyPool(["k"]), "m")
    out = run(classify_message(router, "everything ok?"))
    assert out["intent"] == "status"
