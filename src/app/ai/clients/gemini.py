"""Gemini provider — lean port of Yuki's `services/ai/clients/gemini.py`.

Single-prompt shape (PocketSRE's LLMProvider protocol), sync SDK call in a
thread with a hard timeout, error normalization into LLMAPIError /
LLMRateLimitError.
"""

import asyncio
from collections.abc import AsyncIterator

from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError, ServerError


class LLMAPIError(RuntimeError):
    pass


class LLMRateLimitError(LLMAPIError):
    pass


def _is_rate_limit(exc: Exception) -> bool:
    if getattr(exc, "code", None) == 429:
        return True
    text = str(exc).lower()
    return "429" in text or "resource exhausted" in text or "quota" in text


class GeminiProvider:
    """LLMProvider protocol implementation for Google Gemini."""

    def _call_sync(
        self,
        api_key: str,
        model: str,
        prompt: str,
        output_token_limit: int,
        system_instruction: str | None,
        response_schema: type | None,
    ) -> str:
        try:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=output_token_limit,
                system_instruction=system_instruction,
                automatic_function_calling={"disable": True},
            )
            if response_schema is not None:
                config.response_schema = response_schema
                config.response_mime_type = "application/json"
            response = client.models.generate_content(
                model=model,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                config=config,
            )
            if response and response.text and response.text.strip():
                return response.text
            raise LLMAPIError("Received empty or invalid response from Gemini API.")
        except (ClientError, APIError) as exc:
            if _is_rate_limit(exc):
                raise LLMRateLimitError(f"Gemini rate limit: {exc!r}") from exc
            raise LLMAPIError(f"Gemini API error: {exc!r}") from exc
        except ServerError as exc:
            raise LLMAPIError(f"Gemini server error: {exc!r}") from exc
        except (LLMAPIError, LLMRateLimitError):
            raise
        except Exception as exc:
            raise LLMAPIError(f"Unexpected Gemini error: {exc!r}") from exc

    async def generate(
        self,
        *,
        api_key: str,
        model: str,
        prompt: str,
        timeout_seconds: float,
        output_token_limit: int = 1024,
        system_instruction: str | None = None,
        response_schema: type | None = None,
    ) -> str:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(
                    self._call_sync,
                    api_key,
                    model,
                    prompt,
                    output_token_limit,
                    system_instruction,
                    response_schema,
                ),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise LLMAPIError(
                f"Gemini API timeout after {timeout_seconds} seconds"
            ) from exc

    async def stream(self, *, api_key: str, model: str, prompt: str, timeout_seconds: float) -> AsyncIterator[str]:
        yield await self.generate(
            api_key=api_key, model=model, prompt=prompt, timeout_seconds=timeout_seconds
        )
