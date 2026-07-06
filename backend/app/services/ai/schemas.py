from pydantic import BaseModel, Field


class GeneratedPrompt(BaseModel):
    """Structured response for a generated prompt."""

    text: str = Field(..., description="The generated image prompt")
    theme: str = Field(..., description="The theme used for generation")
    category: str = Field(..., description="The category of the prompt")
    difficulty: str = Field(..., description="The difficulty level (e.g. easy, medium, hard)")


class GeneratedImage(BaseModel):
    """Structured response for a generated image."""

    image_bytes: bytes
    mime_type: str = "image/jpeg"
