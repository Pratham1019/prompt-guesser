import asyncio
import time

import httpx

from app.config import settings
from app.logging import logger
from app.services.ai.exceptions import ImageGenerationError
from app.services.ai.image.base import BaseImageGenerator
from app.services.ai.schemas import GeneratedImage


class HuggingFaceImageGenerator(BaseImageGenerator):
    """
    Generates images using the Hugging Face serverless Inference API.
    Specifically optimized for black-forest-labs/FLUX.1-schnell model.
    """

    def __init__(self) -> None:
        # Verify HF credentials are configured
        if not settings.HF_API_TOKEN or settings.HF_API_TOKEN == "your-hf-token-here":
            raise ImageGenerationError("HF_API_TOKEN is not configured in settings.")

        self.api_url = f"https://api-inference.huggingface.co/models/{settings.HF_IMAGE_MODEL}"
        self.headers = {"Authorization": f"Bearer {settings.HF_API_TOKEN}"}
        self.retry_count = settings.AI_RETRY_COUNT
        self.timeout = settings.AI_TIMEOUT_SECONDS

    async def generate_image(self, prompt: str) -> GeneratedImage:
        logger.info(f"Starting Hugging Face image generation for model: {settings.HF_IMAGE_MODEL}")
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            last_exception = None
            for attempt in range(self.retry_count):
                try:
                    response = await client.post(
                        self.api_url,
                        headers=self.headers,
                        json={"inputs": prompt},
                        timeout=self.timeout,
                    )

                    # Check for success
                    if response.status_code == 200:
                        image_bytes = response.content
                        if not image_bytes:
                            raise ImageGenerationError(
                                "Hugging Face provider returned empty content."
                            )

                        duration = time.time() - start_time
                        logger.info(
                            "Hugging Face image generation succeeded.",
                            extra={"attempt": attempt + 1, "duration": duration},
                        )
                        return GeneratedImage(image_bytes=image_bytes)

                    # Handle Model Loading (503 Service Unavailable)
                    elif response.status_code == 503:
                        try:
                            err_data = response.json()
                            est_time = err_data.get("estimated_time", 10.0)
                        except Exception:
                            est_time = 10.0

                        logger.warning(
                            f"Hugging Face model is loading. Estimated time: {est_time}s. Retrying...",
                            extra={"attempt": attempt + 1, "max_attempts": self.retry_count},
                        )
                        sleep_time = min(est_time, 15.0)
                        await asyncio.sleep(sleep_time)
                        continue

                    # Handle Rate Limit (429 Too Many Requests)
                    elif response.status_code == 429:
                        logger.warning(
                            "Hugging Face rate limited (429). Retrying after backoff...",
                            extra={"attempt": attempt + 1},
                        )
                        await asyncio.sleep(2**attempt)
                        continue

                    # Permanent failures
                    elif response.status_code == 401:
                        raise ImageGenerationError(
                            "Hugging Face authentication failed. Invalid token."
                        )
                    elif response.status_code == 404:
                        raise ImageGenerationError(
                            f"Hugging Face model '{settings.HF_IMAGE_MODEL}' not found."
                        )
                    else:
                        err_msg = f"HTTP {response.status_code}: {response.text}"
                        raise ImageGenerationError(f"Hugging Face Inference API error: {err_msg}")

                except httpx.HTTPError as he:
                    last_exception = he
                    logger.warning(
                        f"Hugging Face request failed: {he}. Retrying...",
                        extra={"attempt": attempt + 1},
                    )
                    await asyncio.sleep(2**attempt)

            raise ImageGenerationError(
                f"Hugging Face image generation failed after {self.retry_count} attempts. Last error: {last_exception}"
            )
