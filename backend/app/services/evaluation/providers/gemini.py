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
        description="Constructive hint for the player helping them find what is missing. Keep it extremely brief (strictly under 15 words). No emojis.",
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

# Core Philosophy
Your main objective is to answer: "Did the player correctly understand the image?"
Do NOT evaluate whether the player reproduced the exact original prompt word-for-word. Reward conceptual understanding over prompt engineering.

# Strictness Calibration
Be strict about missing major concepts. Do NOT award high scores (80% or above) for generic or incomplete descriptions:
- Capping Constraint: If even one major concept (such as the main environment, location setting, time of day, or key secondary objects) is completely missing from the guess, you must cap the similarity_score at a maximum of 80.0.
- Capping Constraint: A guess that only identifies the primary subject and action, but misses the setting or secondary details, must receive a score between 50.0 and 75.0.
- High Scores (90.0+): Only award 90.0 or above if all major concepts are successfully captured in the player's guess.

# Major vs. Minor Concepts
You must separate concepts into Major and Minor categories:
1. Major Concepts (Crucial for the score - 97% of total weight):
   - Primary Subject & Objects (35% weight)
   - Actions & Interactions (20% weight)
   - Environment, Setting, Visually Obvious Location, Time of Day, or Weather (20% weight)
   - Secondary Important Objects (10% weight)
   - Important Relationships/Placements between objects/subjects (10% weight)
   - Examples: "dragon", "astronaut", "flying", "Himalayas", "sunrise", "Mumbai", "auto rickshaw".

2. Minor Concepts (Trivial modifiers - 3% of total weight):
   - Artistic Style & Rendering Medium (e.g., fantasy art, digital painting, oil painting, cinematic) (3% weight)
   - Lighting & Composition (e.g., dramatic lighting, volumetric lighting, camera lens/angle) (1% weight)
   - Mood & Color Palette (e.g., vibrant pastel, dark and gritty) (1% weight)
   - Quality Descriptors or Prompt Adjectives (e.g., masterpiece, ultra detailed, 8k, award winning, photorealistic).

# Synonym Handling
Aggressively reward synonymous concepts. If the player describes the same concept with different words, treat it as a perfect match (e.g., "giant" = "massive", "kid" = "child", "spaceship" = "spacecraft", "relaxing" = "chilling", "city street" = "urban road", "car" = "automobile").

# Semantic Differences
Remain strict when meaningful concepts change. Deduct significant points for major mismatches:
- Vehicle/Object change: Rickshaw vs Taxi -> Deduct meaningful points.
- Action/Location change: Flying above Himalayas vs Sleeping inside a cave -> Deduct significant points.
- Generic vs Specific: Ramen vs Noodles -> This is close, award an extremely high score.

# Score Guidelines
- 100.0: Player successfully identified the image. Meaning is effectively identical. Only trivial wording or minor stylistic differences remain.
- 90.0 - 94.0: Extremely close. All major concepts are correct. Only minor stylistic or descriptive nuances remain.
- 75.0 - 89.0: Strong understanding. One major concept (like setting details or secondary objects) is still incorrect or missing.
- 50.0 - 74.0: Partial understanding. Subject and action are correct, but setting/details are completely missing.
- 20.0 - 49.0: Weak similarity. Only isolated concepts overlap.
- 0.0 - 19.0: Entirely different scene.

# Perfect Score Normalization
If all major concepts are correct and only minor stylistic/descriptive differences remain, the score should naturally be 95.0 or above. If you naturally arrive at a score between 95.0 and 99.9, you should output 100.0.

# Feedback & Hint Guidelines
- Prioritize MAJOR concepts. Do NOT repeatedly mention style, lighting, or render engine unless they are critical.
- Keep the hint actionable, natural, and strictly under 15 words.
- Do NOT use emojis. Keep it plain text.
- Do NOT reveal the original prompt's hidden details or write the original prompt text in the feedback!

You must output a structured JSON response strictly conforming to the requested schema.
"""


class GeminiEvaluationService(BaseEvaluationService):
    """
    Production-ready semantic evaluator using Gemini's structured output capability.
    Compares guesses and returns score, reasoning, matched/missing concepts, and feedback.
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

            # Implement programmatic Perfect Score Normalization
            final_score = raw_result.similarity_score
            if 95.0 <= final_score <= 99.9:
                minor_indicators = {
                    "style",
                    "lighting",
                    "lens",
                    "camera",
                    "render",
                    "detailed",
                    "artistic",
                    "digital",
                    "painting",
                    "illustration",
                    "cinematic",
                    "mood",
                    "color",
                    "palette",
                    "composition",
                    "photorealistic",
                    "hyperrealistic",
                    "realistic",
                    "8k",
                    "quality",
                    "detail",
                    "concept art",
                    "medium",
                    "descriptor",
                }
                # Check if all listed missing concepts are purely minor / stylistic
                all_minor = True
                for concept in raw_result.missing_concepts:
                    concept_lower = concept.lower()
                    if not any(indicator in concept_lower for indicator in minor_indicators):
                        all_minor = False
                        break

                if all_minor:
                    logger.info(
                        f"Normalizing semantic score {final_score} to 100.0. "
                        f"Remaining missing concepts are purely minor/stylistic: {raw_result.missing_concepts}"
                    )
                    final_score = 100.0

            logger.info(
                "Semantic evaluation completed successfully.",
                extra={
                    "duration_seconds": duration,
                    "original_score": raw_result.similarity_score,
                    "final_score": final_score,
                    "confidence": raw_result.confidence_score,
                },
            )

            return EvaluationResult(
                score=final_score,
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
