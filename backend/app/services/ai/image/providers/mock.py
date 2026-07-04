from app.logging import logger
from app.services.ai.image.base import BaseImageGenerator
from app.services.ai.schemas import GeneratedImage


class MockImageGenerator(BaseImageGenerator):
    """
    Mock image generator that returns a fixed dummy image byte sequence
    for testing and offline local development.
    """

    async def generate_image(self, prompt: str) -> GeneratedImage:
        logger.info(f"Mock image generator called with prompt: {prompt}")

        # A tiny valid 1x1 PNG byte sequence
        dummy_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x01"
            b"\x00\x00\x0c\x00\x01\x04\x06\xf0\x1f\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return GeneratedImage(image_bytes=dummy_png)
