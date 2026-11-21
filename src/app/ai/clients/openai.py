"""OpenAI-compatible provider — lean port of Yuki's `services/ai/clients/openai.py`.

Works against OpenAI and OpenAI-compatible endpoints (OpenRouter etc. via
`base_url`). Single-prompt shape per PocketSRE's LLMProvider protocol.
"""

import asyncio
from collections.abc import AsyncIterator

import openai
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
)

from app.ai.clients.gemini import LLMAPIError, LLMRateLimitError


class OpenAIProvider:
    """LLMProvider protocol implementation for OpenAI-compatible chat APIs."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url

    async def generate(
        self,
        *,
        api_key: str,
        model: str,
        prompt: str,
        timeout_seconds: float,
        output_token_limit: int = 1024,
        system_instruction: str | None = None,
    ) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        try:
            client = openai.AsyncOpenAI(
                api_key=api_key, base_url=self._base_url, timeout=timeout_seconds
            )
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=output_token_limit,
            )
            if not response.choices:
                raise LLMAPIError("API returned no choices")
            choice = response.choices[0]
            if choice.finish_reason == "content_filter":
                raise LLMAPIError("Response blocked by content filter")
            content = choice.message.content
            if content and content.strip():
                return content.strip()
            refusal = getattr(choice.message, "refusal", None)
            if refusal:
                raise LLMAPIError(f"Model refusal: {refusal}")
            raise LLMAPIError(
                f"Empty response (finish_reason: {choice.finish_reason})"
            )
        except (AuthenticationError, PermissionDeniedError, BadRequestError) as exc:
            raise LLMAPIError(f"OpenAI client error: {exc!r}") from exc
        except RateLimitError as exc:
            raise LLMRateLimitError(f"OpenAI rate limit: {exc!r}") from exc
        except (InternalServerError, APITimeoutError, APIConnectionError) as exc:
            raise LLMAPIError(f"OpenAI retryable error: {exc!r}") from exc
        except (LLMAPIError, LLMRateLimitError):
            raise
        except asyncio.TimeoutError as exc:
            raise LLMAPIError(
                f"OpenAI timeout after {timeout_seconds} seconds"
            ) from exc
        except Exception as exc:
            raise LLMAPIError(f"Unexpected OpenAI error: {exc!r}") from exc

    async def stream(self, *, api_key: str, model: str, prompt: str, timeout_seconds: float) -> AsyncIterator[str]:
        yield await self.generate(
            api_key=api_key, model=model, prompt=prompt, timeout_seconds=timeout_seconds
        )
