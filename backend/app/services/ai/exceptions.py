class AIError(Exception):
    """Base exception for all AI service errors."""

    pass


class PromptGenerationError(AIError):
    """Raised when prompt generation fails or validation fails."""

    pass


class ImageGenerationError(AIError):
    """Raised when image generation fails."""

    pass


class EmbeddingGenerationError(AIError):
    """Raised when embedding generation fails or dimension mismatch occurs."""

    pass


class AIClientConfigurationError(AIError):
    """Raised when AI client configuration is missing or invalid."""

    pass
