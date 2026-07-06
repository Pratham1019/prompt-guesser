import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.services.evaluation.providers.gemini import GeminiEvaluationSchema, GeminiEvaluationService


async def test_normalization_success():
    # Scenario 1: Model returns 98.5 but only minor/stylistic differences remain.
    # It should be normalized to 100.0.
    mock_ai_client = MagicMock()
    mock_parsed_result = GeminiEvaluationSchema(
        similarity_score=98.5,
        matched_concepts=["dragon", "Himalayas", "flying", "sunrise"],
        missing_concepts=["fantasy concept art style", "cinematic lighting"],
        reasoning="All major elements matched. Minor style is missing.",
        player_feedback="Awesome job! Just missing the style.",
        confidence_score=0.98,
    )

    mock_ai_client.generate_text_structured = AsyncMock(return_value=mock_parsed_result)

    service = GeminiEvaluationService(ai_client=mock_ai_client)
    result = await service.evaluate(
        "dragon flying Himalayas", "dragon flying Himalayas in fantasy concept art"
    )

    assert result.score == 100.0, f"Expected normalized score 100.0, got {result.score}"
    print("[OK] Test Passed: Successfully normalized 98.5 to 100.0 for minor missing concepts.")


async def test_normalization_no_trigger_on_major():
    # Scenario 2: Model returns 98.0 but a major setting/object is missing (e.g. not minor).
    # It should NOT be normalized to 100.0.
    mock_ai_client = MagicMock()
    mock_parsed_result = GeminiEvaluationSchema(
        similarity_score=98.0,
        matched_concepts=["dragon", "flying"],
        missing_concepts=["Himalayas location"],  # Location is a major concept!
        reasoning="Subject and action matched. Location missing.",
        player_feedback="You missed the location setting.",
        confidence_score=0.95,
    )

    mock_ai_client.generate_text_structured = AsyncMock(return_value=mock_parsed_result)

    service = GeminiEvaluationService(ai_client=mock_ai_client)
    result = await service.evaluate("dragon flying", "dragon flying Himalayas")

    assert result.score == 98.0, f"Expected un-normalized score 98.0, got {result.score}"
    print("[OK] Test Passed: Did not normalize 98.0 since a major concept (location) was missing.")


async def test_normalization_no_trigger_on_low_score():
    # Scenario 3: Model returns 95.0 (below 97.0 threshold).
    # It should NOT be normalized to 100.0 even if missing concepts are minor.
    mock_ai_client = MagicMock()
    mock_parsed_result = GeminiEvaluationSchema(
        similarity_score=95.0,
        matched_concepts=["dragon", "flying"],
        missing_concepts=["digital art style"],
        reasoning="Core matched. Style missing.",
        player_feedback="Missed the style.",
        confidence_score=0.90,
    )

    mock_ai_client.generate_text_structured = AsyncMock(return_value=mock_parsed_result)

    service = GeminiEvaluationService(ai_client=mock_ai_client)
    result = await service.evaluate("dragon flying", "dragon flying digital art")

    assert result.score == 95.0, f"Expected un-normalized score 95.0, got {result.score}"
    print("[OK] Test Passed: Did not normalize 95.0 because it is below the 97.0 threshold.")


async def main():
    print("=========================================")
    print("STARTING EVALUATOR NORMALIZATION TESTS")
    print("=========================================")
    await test_normalization_success()
    await test_normalization_no_trigger_on_major()
    await test_normalization_no_trigger_on_low_score()
    print("=========================================")
    print("ALL EVALUATOR NORMALIZATION TESTS PASSED")
    print("=========================================")


if __name__ == "__main__":
    asyncio.run(main())
