from abc import ABC, abstractmethod

from app.services.ai.schemas import GeneratedImage


class BaseImageGenerator(ABC):
    """
    Abstract base class for all image generation providers.
    """

    @abstractmethod
    async def generate_image(self, prompt: str) -> GeneratedImage:
        """
        Generates an image from a text prompt.
        Returns GeneratedImage schema containing the raw image bytes.
        """
        pass
