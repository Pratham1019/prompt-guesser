from app.config import settings
from app.services.ai.image.base import BaseImageGenerator
from app.services.ai.image.providers.huggingface import HuggingFaceImageGenerator
from app.services.ai.image.providers.mock import MockImageGenerator


def get_image_generator() -> BaseImageGenerator:
    """
    Dependency injection factory that returns the configured image generator instance.
    """
    provider = settings.IMAGE_PROVIDER.lower()
    if provider == "huggingface":
        return HuggingFaceImageGenerator()
    elif provider == "mock":
        return MockImageGenerator()
    else:
        # Default to HuggingFace
        return HuggingFaceImageGenerator()
