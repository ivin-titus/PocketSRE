"""Build an LLMRouter from settings; None when the provider has no keys."""

from app.ai.clients.gemini import GeminiProvider
from app.ai.clients.openai import OpenAIProvider
from app.ai.key_pool import KeyPool
from app.ai.router import LLMRouter
from app.config import Settings


def build_llm_router(settings: Settings) -> LLMRouter | None:
    provider = settings.ai_provider.lower()
    if provider == "gemini":
        keys = settings.gemini_keys
        if not keys:
            return None
        return LLMRouter(GeminiProvider(), KeyPool(keys), settings.gemini_model)
    if provider == "openai":
        if not settings.openai_api_key:
            return None
        return LLMRouter(
            OpenAIProvider(settings.openai_base_url or None),
            KeyPool([settings.openai_api_key]),
            settings.openai_model,
        )
    return None
