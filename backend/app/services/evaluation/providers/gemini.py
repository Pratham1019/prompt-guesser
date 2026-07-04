import time
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.logging import logger
from app.services.ai.client import AIClient
from app.services.evaluation.base import BaseEvaluationService, EvaluationResult


class GeminiEvaluationSchema(BaseModel):
    """
    Pydantic schema used to request structured output from Gemini
    for semantic prompt comparison.
    """

    similarity_score: float = Field(
        ...,
        description="A float score between 0.0 and 100.0 indicating how closely the player's guess matches the meaning of the original prompt.",
    )
    matched_concepts: list[str] = Field(
        ...,
        description="List of key elements, subjects, styles, actions, or modifiers correctly captured in the guess.",
    )
    missing_concepts: list[str] = Field(
        ...,
        description="List of key concepts or details present in the original prompt but missing in the player's guess.",
    )
    reasoning: str = Field(
        ...,
        description="Internal explanation of the evaluation rationale and score calculation.",
    )
    player_feedback: str = Field(
        ...,
        description="Encouraging, constructive hint for the player helping them find what is missing (without revealing the original prompt itself).",
    )
    confidence_score: float = Field(
        ...,
        description="A float confidence value between 0.0 and 1.0 reflecting model certainty in the evaluation.",
    )

    @field_validator("similarity_score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError("similarity_score must be between 0.0 and 100.0")
        return round(v, 2)

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return round(v, 2)


EVALUATION_SYSTEM_PROMPT = """
You are a semantic similarity evaluator for a prompt-guessing game. Your task is to evaluate a player's guess against an original target prompt and produce a structured evaluation.

Evaluate based on meaning and concepts rather than exact word-for-word matching. A player using different words or synonyms to describe the same concept should be rewarded equally.

Consider the following evaluation categories:
1. Primary Subject & Objects (e.g., character, animal, object, core entity)
2. Actions & Interactions (e.g., swimming, flying, holding, sitting)
3. Environment & Setting (e.g., Tokyo streets, Mars, heavy rain, underwater)
4. Artistic Style & Medium (e.g., digital illustration, cinematic photo, oil painting, watercolor)
5. Lighting & Composition (e.g., golden hour, close-up, low-angle, cinematic lighting)
6. Mood & Color Palette (e.g., vibrant pastel, whimsical, dark and gritty)

Scoring Guidelines:
- 100.0: Perfect semantic equivalent. Meaning is identical, even if phrasing is different.
- 90.0 - 99.0: Captures all key concepts (subject, environment, style, lighting) with only minor descriptive nuances missing.
- 70.0 - 89.0: Captures the main subject and setting, but omits style, composition, or lighting details.
- 40.0 - 69.0: Captures the subject but misses the entire environment/style, or vice versa (e.g., "A fish in Tokyo" vs "A giant koi fish swimming through Tokyo streets during heavy rain").
- 10.0 - 39.0: Weak match. Captures isolated words or a broad general category, but misses the core action and context.
- 0.0 - 9.0: Completely unrelated.

Feedback Guidelines:
- Write concise, constructive feedback helping the player refine their next guess.
- Describe what they matched and what general category of details they missed (e.g., "You got the subject right, but you need to specify the environment and style.").
- CRITICAL: Do NOT reveal the original prompt's hidden details or write the original prompt text in the feedback!

You must output a structured JSON response strictly conforming to the requested schema.
"""


class GeminiEvaluationService(BaseEvaluationService):
    """
    Production-ready semantic evaluator using Gemini's structured output capability.
    Compare guesses and returns score, reasoning, matched/missing concepts, and feedback.
    """

    def __init__(self, ai_client: Optional[AIClient] = None) -> None:
        self.ai_client = ai_client
        self._fallback_active = False
        if ai_client is None:
            try:
                self.ai_client = AIClient()
            except Exception as e:
                logger.warning(
                    f"Failed to initialize AI client for evaluation: {e}. Active fallback to Jaccard."
                )
                self._fallback_active = True

    async def evaluate(self, guess: str, target: str) -> EvaluationResult:
        start_time = time.time()
        logger.info("Initializing semantic evaluation request.")

        # Construct evaluation prompt
        prompt = (
            f'Original Target Prompt: "{target}"\n'
            f'Player\'s Guess: "{guess}"\n\n'
            f"Please perform the evaluation and return the structured JSON result."
        )

        if self._fallback_active or self.ai_client is None:
            logger.warning(
                "Bypassing Gemini call due to inactive AI client or configuration fallback."
            )
            fallback_score = self._fallback_jaccard(guess, target)
            return EvaluationResult(
                score=fallback_score,
                feedback="We evaluated your guess against the main keywords. Try describing more details of the image!",
                matched_concepts=["Word overlap fallback"],
                missing_concepts=["Unavailable during fallback"],
                reasoning="AI client is unconfigured or failed during construction.",
                confidence_score=0.0,
            )

        try:
            # Inject system prompt
            full_prompt = f"{EVALUATION_SYSTEM_PROMPT}\n\n{prompt}"

            # Request structured output via AIClient
            raw_result = await self.ai_client.generate_text_structured(
                full_prompt, GeminiEvaluationSchema
            )
            duration = time.time() - start_time
            logger.info(
                "Semantic evaluation completed successfully.",
                extra={
                    "duration_seconds": duration,
                    "score": raw_result.similarity_score,
                    "confidence": raw_result.confidence_score,
                },
            )

            return EvaluationResult(
                score=raw_result.similarity_score,
                feedback=raw_result.player_feedback,
                matched_concepts=raw_result.matched_concepts,
                missing_concepts=raw_result.missing_concepts,
                reasoning=raw_result.reasoning,
                confidence_score=raw_result.confidence_score,
            )

        except Exception as e:
            logger.error(f"Semantic evaluation failed: {e}")
            # Fall back to Jaccard similarity if Gemini API fails entirely to prevent game loop crash
            logger.warning(
                "Falling back to local Jaccard overlap similarity due to evaluator failure."
            )
            fallback_score = self._fallback_jaccard(guess, target)
            return EvaluationResult(
                score=fallback_score,
                feedback="We evaluated your guess against the main keywords. Try describing more details of the image!",
                matched_concepts=["Word overlap fallback"],
                missing_concepts=["Unavailable during fallback"],
                reasoning=f"Provider failed: {e}",
                confidence_score=0.0,
            )

    def _fallback_jaccard(self, guess: str, target: str) -> float:
        """Simple fallback calculator to prevent crashing in production."""
        guess_words = set(guess.strip().lower().split())
        target_words = set(target.strip().lower().split())
        if not guess_words or not target_words:
            return 0.0
        intersection = guess_words.intersection(target_words)
        union = guess_words.union(target_words)
        return round(float(len(intersection) / len(union) * 100.0), 2)
