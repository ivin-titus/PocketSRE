"""Provider boundary adapted from Yuki's vendor-client interface."""

from collections.abc import AsyncIterator
from typing import Protocol


class LLMProvider(Protocol):
    async def generate(
        self, *, api_key: str, model: str, prompt: str, timeout_seconds: float
    ) -> str: ...

    async def stream(
        self, *, api_key: str, model: str, prompt: str, timeout_seconds: float
    ) -> AsyncIterator[str]: ...
