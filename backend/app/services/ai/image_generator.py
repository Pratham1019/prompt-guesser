from typing import Optional

from app.services.ai.client import AIClient
from app.services.ai.image import get_image_generator
from app.services.ai.schemas import GeneratedImage


class ImageGeneratorService:
    """
    Orchestration service wrapper that resolves the configured image provider
    and delegates image generation to it.
    """

    def __init__(self, client: Optional[AIClient] = None) -> None:
        self.provider = get_image_generator()

    async def generate_image(self, prompt: str) -> GeneratedImage:
        """
        Generates an image from a prompt using the active configured provider.
        """
        return await self.provider.generate_image(prompt)
