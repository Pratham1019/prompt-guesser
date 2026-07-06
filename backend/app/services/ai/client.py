import asyncio
import time
from typing import Awaitable, Callable, Type, TypeVar, cast

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings
from app.logging import logger
from app.services.ai.exceptions import AIClientConfigurationError, AIError

R = TypeVar("R")
T = TypeVar("T", bound=BaseModel)


class AIClient:
    """
    Core client for communicating with AI providers.
    Abstracts SDK logic, authentication, retries, and structured responses.
    """

    def __init__(self) -> None:
        if not settings.AI_API_KEY or settings.AI_API_KEY == "your-ai-api-key-here":
            raise AIClientConfigurationError("AI_API_KEY is not configured in settings.")

        # Initialize the official google-genai client
        self.client = genai.Client(api_key=settings.AI_API_KEY)
        self.retry_count = settings.AI_RETRY_COUNT
        self.timeout = settings.AI_TIMEOUT_SECONDS

    async def _execute_with_retry(self, operation: Callable[[], Awaitable[R]], context: str) -> R:
        """Executes an async operation with exponential backoff retries."""
        last_exception: Exception | None = None
        for attempt in range(self.retry_count):
            try:
                start_time = time.time()
                result = await asyncio.wait_for(operation(), timeout=self.timeout)
                duration = time.time() - start_time
                logger.info(
                    f"AI operation '{context}' succeeded.",
                    extra={"attempt": attempt + 1, "duration": duration},
                )
                return result
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(
                    f"AI operation '{context}' timed out.",
                    extra={"attempt": attempt + 1, "max_attempts": self.retry_count},
                )
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"AI operation '{context}' failed: {str(e)}",
                    extra={"attempt": attempt + 1, "max_attempts": self.retry_count},
                )

            if attempt < self.retry_count - 1:
                await asyncio.sleep(2**attempt)

        logger.error(
            f"AI operation '{context}' completely failed after {self.retry_count} attempts."
        )
        raise AIError(f"Failed to execute '{context}': {str(last_exception)}") from last_exception

    async def generate_text_structured(self, prompt: str, schema: Type[T]) -> T:
        """Generates structured JSON output strictly conforming to a Pydantic schema."""
        # Model fallback priority sequence
        models_priority = [
            settings.AI_TEXT_MODEL,  # Main model (e.g. gemini-3.1-flash-lite)
            "gemini-2.5-flash-lite",  # Fallback 1
            "gemini-2.5-flash",  # Fallback 2
            "gemini-1.5-flash",  # Fallback 3
        ]

        # Deduplicate models while keeping order
        seen = set()
        models_to_try = [x for x in models_priority if not (x in seen or seen.add(x))]

        last_exception = None
        for model_name in models_to_try:
            try:
                logger.info(f"Attempting structured generation with model: {model_name}")

                async def _op(m_name=model_name) -> T:
                    response = await self.client.aio.models.generate_content(
                        model=m_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=schema,
                            temperature=0.7,
                        ),
                    )

                    if hasattr(response, "parsed") and response.parsed is not None:
                        return cast(T, response.parsed)

                    # Fallback manual parsing just in case
                    if not response.text:
                        raise Exception("No text response returned by the AI provider.")
                    return schema.model_validate_json(response.text)

                return await self._execute_with_retry(_op, f"generate_text_structured_{model_name}")
            except Exception as e:
                logger.warning(
                    f"Model {model_name} failed during structured generation: {e}. Proceeding to next fallback."
                )
                last_exception = e

        logger.error("All configured Gemini models failed during structured generation.")
        raise AIError(
            f"All Gemini models failed. Last error: {str(last_exception)}"
        ) from last_exception
