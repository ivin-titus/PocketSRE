"""Retry and backpressure semantics adapted from Yuki's LLM interface."""

import asyncio

from app.ai.key_pool import KeyPool, KeyPoolRateLimitError
from app.ai.providers import LLMProvider


class LLMUnavailableError(RuntimeError):
    pass


class LLMRouter:
    def __init__(self, provider: LLMProvider, key_pool: KeyPool, model: str, max_retries: int = 2) -> None:
        self.provider = provider
        self.key_pool = key_pool
        self.model = model
        self.max_retries = max_retries

    async def generate(self, prompt: str, timeout_seconds: float) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                key = await self.key_pool.acquire()
            except KeyPoolRateLimitError as exc:
                if exc.retry_after >= timeout_seconds:
                    raise LLMUnavailableError("All provider keys are rate limited") from exc
                await asyncio.sleep(exc.retry_after)
                continue
            try:
                response = await self.provider.generate(
                    api_key=key, model=self.model, prompt=prompt, timeout_seconds=timeout_seconds
                )
                await self.key_pool.record_success(key)
                return response
            except Exception as exc:  # provider exceptions are intentionally normalized here
                last_error = exc
                await self.key_pool.record_failure(key)
                if attempt < self.max_retries:
                    await asyncio.sleep(0.1 * (2**attempt))
        raise LLMUnavailableError("Provider request failed") from last_error
