import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from app.services.evaluation.providers import GeminiEvaluationService

load_dotenv()


async def run_scenario(eval_svc: GeminiEvaluationService, target: str, guess: str, name: str):
    print("\n=========================================")
    print(f"RUNNING SCENARIO: {name}")
    print(f'Target: "{target}"')
    print(f'Guess:  "{guess}"')
    print("=========================================")

    result = await eval_svc.evaluate(guess, target)

    print(f"Similarity Score:  {result.score}/100")
    print(f"Confidence Score:  {result.confidence_score}")
    print(f"Matched Concepts:  {result.matched_concepts}")
    print(f"Missing Concepts:  {result.missing_concepts}")
    print(f"Reasoning:         {result.reasoning}")
    print(f"Player Feedback:   {result.feedback}")


async def main():
    api_key = os.getenv("AI_API_KEY", "")
    if not api_key or api_key == "your-ai-api-key-here":
        print(
            "WARNING: AI_API_KEY is not configured or is a placeholder. Tests will run in Local Fallback mode."
        )
    else:
        print("AI_API_KEY is detected. Running tests against the real Gemini Model.")

    eval_svc = GeminiEvaluationService()

    target = "A giant koi fish swimming through the streets of Tokyo during heavy rain."

    # Scenario 1: Perfect match (phrased slightly differently)
    await run_scenario(
        eval_svc,
        target=target,
        guess="A giant koi fish swimming through Tokyo streets in heavy rain.",
        name="Perfect Match",
    )

    # Scenario 2: Partial match (some details missing)
    await run_scenario(
        eval_svc,
        target=target,
        guess="A huge fish swimming through a rainy city.",
        name="Partial Match",
    )

    # Scenario 3: Weak match (unrelated subjects)
    await run_scenario(
        eval_svc, target=target, guess="A futuristic spaceship above Mars.", name="Weak Match"
    )

    # Scenario 4: Near-perfect wording differences (synonymous phrasing)
    await run_scenario(
        eval_svc,
        target=target,
        guess="A massive colored carp navigating Tokyo's flooded avenues amidst a downpour.",
        name="Near-perfect wording differences (Synonyms)",
    )


if __name__ == "__main__":
    asyncio.run(main())
