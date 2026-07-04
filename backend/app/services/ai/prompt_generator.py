from app.logging import logger
from app.services.ai.client import AIClient
from app.services.ai.exceptions import PromptGenerationError
from app.services.ai.schemas import GeneratedPrompt


class PromptGeneratorService:
    """
    Generates high-quality prompts suitable for Daily Challenges.
    Supports configurable themes and difficulties.
    """

    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def generate_daily_challenge_prompt(self) -> GeneratedPrompt:
        """
        Generates a new prompt for a Daily Challenge.
        Ensures high quality and variability.
        """
        system_instructions = (
            "You are an expert AI artist and prompt engineer. "
            "Your task is to generate a highly detailed, visually striking prompt for an image generation model. "
            "The prompt must be safe for work, highly creative, and suitable for a daily challenge game. "
            "Respond ONLY with a valid JSON matching the required schema."
        )

        try:
            prompt_data = await self.client.generate_text_structured(
                prompt=system_instructions,
                schema=GeneratedPrompt,
            )

            # Additional validations can be performed here (e.g. duplicate detection via db check)
            self._validate_prompt(prompt_data)
            return prompt_data

        except Exception as e:
            logger.error(f"Failed to generate daily challenge prompt: {e}")
            raise PromptGenerationError(f"Prompt generation failed: {e}") from e

    def _validate_prompt(self, prompt: GeneratedPrompt) -> None:
        """Validates the generated prompt text to ensure it meets quality standards."""
        if len(prompt.text) < 20:
            raise PromptGenerationError(
                "Generated prompt is too short. Must be at least 20 characters."
            )
        if len(prompt.text) > 1000:
            raise PromptGenerationError(
                "Generated prompt is too long. Must be under 1000 characters."
            )
