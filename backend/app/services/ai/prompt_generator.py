from datetime import date
from typing import Optional

from app.logging import logger
from app.services.ai.client import AIClient
from app.services.ai.exceptions import PromptGenerationError
from app.services.ai.schemas import GeneratedPrompt


class PromptGeneratorService:
    """
    Generates prompts for Daily Challenges from a curated, fixed set of 30 prompts
    to ensure high-quality and deterministic challenges.
    """

    FIXED_PROMPTS = [
        "A monkey driving a yellow auto rickshaw through a futuristic city during sunset.",
        "An astronaut drinking chai while sitting on the Moon, Earth glowing in the background.",
        "A giant elephant walking through the streets of Mumbai during heavy rain.",
        "A dragon flying above the Himalayas at sunrise, fantasy concept art.",
        "A dog working as a chef in a busy Italian restaurant, Pixar-style 3D render.",
        "A pirate ship sailing through fluffy white clouds instead of the ocean.",
        "A tiger peacefully sleeping inside a modern library surrounded by books.",
        "A whale flying above New York City with airplanes flying beside it.",
        "A lighthouse floating in the sky held up by giant colorful balloons.",
        "A cat reading a book inside a floating castle above the clouds.",
        "A giant turtle carrying an entire city on its shell while drifting through outer space.",
        "A panda enjoying street food at a crowded night market filled with lanterns.",
        "A train traveling across Saturn's rings beneath a colorful nebula.",
        "A lion sitting in a classroom while students take notes.",
        "A magical tree growing from the middle of a busy highway.",
        "A spaceship landing in the middle of a green rice field during golden hour.",
        "A crystal wolf standing on a frozen lake beneath the northern lights.",
        "A peacock spreading its feathers in front of the Taj Mahal at sunrise.",
        "A boy fishing from the edge of Saturn's rings while wearing a space suit.",
        "A castle built entirely from transparent glass surrounded by giant waterfalls.",
        "A bicycle parked on the surface of Mars beneath a sky full of stars.",
        "A robot watering flowers in a peaceful village during spring.",
        "A giant octopus wrapped around an ancient lighthouse during a thunderstorm.",
        "A deer glowing softly while standing inside a forest filled with blue flowers at night.",
        "A football match being played on top of a floating island above the clouds.",
        "A camel standing alone on a snowy mountain peak during sunrise.",
        "A giant clock floating above a peaceful village at sunset.",
        "A child flying a kite on the surface of the Moon while Earth rises in the distance.",
        "A waterfall flowing upward into the sky from the middle of a dense forest.",
        "A hot air balloon shaped like an elephant flying over a colorful jungle at sunrise.",
    ]

    def __init__(self, client: AIClient) -> None:
        self.client = client

    async def generate_daily_challenge_prompt(
        self, target_date: Optional[date] = None
    ) -> GeneratedPrompt:
        """
        Selects a prompt from the fixed set of 30 prompts deterministically based on target date.
        Ensures idempotency for challenge generation.
        """
        if not target_date:
            target_date = date.today()

        try:
            # Deterministic selection based on date ordinal
            idx = target_date.toordinal() % len(self.FIXED_PROMPTS)
            prompt_text = self.FIXED_PROMPTS[idx]

            logger.info(
                f"Selected prompt deterministically for date {target_date} (Index: {idx}): {prompt_text}"
            )

            prompt_data = GeneratedPrompt(
                text=prompt_text,
                theme="Fantasy",
                category="Creative",
                difficulty="medium",
            )

            self._validate_prompt(prompt_data)
            return prompt_data

        except Exception as e:
            logger.error(f"Failed to select prompt: {e}")
            raise PromptGenerationError(f"Prompt generation failed: {e}") from e

    def _validate_prompt(self, prompt: GeneratedPrompt) -> None:
        """Validates the generated prompt text to ensure it meets quality standards."""
        if len(prompt.text) < 10:
            raise PromptGenerationError(
                "Selected prompt is too short. Must be at least 10 characters."
            )
        if len(prompt.text) > 1000:
            raise PromptGenerationError(
                "Selected prompt is too long. Must be under 1000 characters."
            )
