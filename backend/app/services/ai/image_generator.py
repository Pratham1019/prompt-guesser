from app.logging import logger
from app.services.ai.client import AIClient
from app.services.ai.exceptions import ImageGenerationError
from app.services.ai.schemas import GeneratedImage


class ImageGeneratorService:
    """
    Generates images from prompts using the configured AI image model.
    """

    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def generate_image(self, prompt: str) -> GeneratedImage:
        """
        Requests an image generation for the provided prompt.
        Validates the output before returning.
        """
        try:
            image_bytes = await self.client.generate_image(prompt)
            if not image_bytes:
                raise ImageGenerationError("Received empty image bytes from AI client.")

            # Additional validation of image bytes (like magic numbers for JPEG) can be done here.
            return GeneratedImage(image_bytes=image_bytes)
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            raise ImageGenerationError(f"Image generation failed: {e}") from e
