import io

from huggingface_hub import AsyncInferenceClient
from huggingface_hub.utils import HfHubHTTPError

from app.config import settings
from app.logging import logger
from app.services.ai.exceptions import ImageGenerationError
from app.services.ai.image.base import BaseImageGenerator
from app.services.ai.schemas import GeneratedImage


class HuggingFaceImageGenerator(BaseImageGenerator):
    """
    Generates images using the official Hugging Face Hub AsyncInferenceClient.
    Bypasses legacy DNS/subdomain errors by utilizing the client's automated routing.
    """

    def __init__(self) -> None:
        # Verify HF credentials are configured
        if not settings.HF_API_TOKEN or settings.HF_API_TOKEN == "your-hf-token-here":
            raise ImageGenerationError("HF_API_TOKEN is not configured in settings.")

        self.client = AsyncInferenceClient(api_key=settings.HF_API_TOKEN)
        self.model = settings.HF_IMAGE_MODEL

    async def generate_image(self, prompt: str) -> GeneratedImage:
        logger.info(f"Starting Hugging Face image generation using model: {self.model}")

        try:
            # Query the Inference API asynchronously
            # This automatically handles DNS resolution, load-balancing, and API routing
            image = await self.client.text_to_image(
                prompt=prompt,
                model=self.model,
            )

            # Convert PIL Image back to raw JPEG bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="JPEG")
            image_bytes = img_byte_arr.getvalue()

            if not image_bytes:
                raise ImageGenerationError("Hugging Face client returned empty image bytes.")

            logger.info("Hugging Face image generation succeeded.")
            return GeneratedImage(image_bytes=image_bytes)

        except HfHubHTTPError as hf_err:
            err_msg = f"HTTP {hf_err.response.status_code}: {hf_err.message}"
            logger.error(f"Hugging Face Hub API error: {err_msg}")
            raise ImageGenerationError(f"Hugging Face Inference API error: {err_msg}") from hf_err
        except Exception as e:
            logger.error(f"Hugging Face unexpected generation failure: {e}")
            raise ImageGenerationError(f"Hugging Face unexpected error: {e}") from e
