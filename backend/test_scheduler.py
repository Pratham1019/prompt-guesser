import asyncio
import os
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal, engine
from app.models.base import Base
from app.models.challenge import PromptChallenge
from app.services.ai.schemas import GeneratedEmbedding, GeneratedImage, GeneratedPrompt
from app.services.generation import ChallengeGenerationService, GenerationOrchestratorError
from app.services.scheduler import ChallengeSchedulerService


async def reset_db():
    """Drops and recreates all tables in SQLite for testing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def run_scenario_1():
    """
    Scenario 1: Database contains zero future challenges.
    Scheduler generates the configured future buffer.
    """
    print("\n--- Running Scenario 1: Clean DB, Generate Buffer ---")
    await reset_db()

    async with SessionLocal() as db:
        # Override buffer size to 3 for faster testing
        with patch.object(settings, "SCHEDULER_BUFFER_SIZE", 3):
            # Mock generator service pipeline to avoid real API queries
            mock_gen_svc = AsyncMock()
            mock_gen_svc.generate_daily_challenge.side_effect = lambda d: PromptChallenge(
                publish_date=d,
                prompt=f"Mock Prompt for {d}",
                image_url=f"/storage/mock_{d}.jpg",
                target_embedding=[0.01] * 768,
                embedding_model_name="mock-model",
                status="scheduled",
            )

            scheduler = ChallengeSchedulerService(db, generation_svc=mock_gen_svc)

            # Check buffer status
            status = await scheduler.get_buffer_status()
            assert status["active_count"] == 0, (
                f"Expected 0 active future challenges, got {status['active_count']}"
            )
            assert status["missing_count"] == 3, (
                f"Expected 3 missing challenges, got {status['missing_count']}"
            )

            # Populate buffer
            generated = await scheduler.populate_buffer()
            assert len(generated) == 3, f"Expected 3 challenges generated, got {len(generated)}"

            # Verify the call counts and arguments
            today = scheduler.get_local_today()
            expected_dates = [
                today + timedelta(days=1),
                today + timedelta(days=2),
                today + timedelta(days=3),
            ]
            mock_gen_svc.generate_daily_challenge.assert_any_call(expected_dates[0])
            mock_gen_svc.generate_daily_challenge.assert_any_call(expected_dates[1])
            mock_gen_svc.generate_daily_challenge.assert_any_call(expected_dates[2])

            print(
                "✔ Scenario 1 Passed: Successfully checked buffer status and generated 3 challenges."
            )


async def run_scenario_2():
    """
    Scenario 2: Database already contains sufficient future challenges.
    Scheduler performs no work.
    """
    print("\n--- Running Scenario 2: Buffer Compliant, No-Op ---")
    # Reset and seed 3 future challenges
    await reset_db()

    async with SessionLocal() as db:
        today = date.today()
        # Seed 3 future challenges
        for i in range(1, 4):
            c = PromptChallenge(
                publish_date=today + timedelta(days=i),
                prompt=f"Seed Prompt {i}",
                image_url=f"/storage/seed_{i}.jpg",
                target_embedding=[0.01] * 768,
                embedding_model_name="mock-model",
                status="scheduled",
            )
            db.add(c)
        await db.commit()

    async with SessionLocal() as db:
        with patch.object(settings, "SCHEDULER_BUFFER_SIZE", 3):
            mock_gen_svc = AsyncMock()
            scheduler = ChallengeSchedulerService(db, generation_svc=mock_gen_svc)

            status = await scheduler.get_buffer_status()
            assert status["active_count"] == 3, (
                f"Expected 3 active challenges, got {status['active_count']}"
            )
            assert status["missing_count"] == 0, (
                f"Expected 0 missing, got {status['missing_count']}"
            )

            generated = await scheduler.populate_buffer()
            assert len(generated) == 0, f"Expected 0 generated, got {len(generated)}"
            mock_gen_svc.generate_daily_challenge.assert_not_called()

            print("✔ Scenario 2 Passed: Compliant buffer detected, 0 challenges generated.")


async def run_scenario_3():
    """
    Scenario 3: One challenge generation fails.
    Scheduler logs the failure and continues safely.
    """
    print("\n--- Running Scenario 3: Single Challenge Fails, Recover & Continue ---")
    await reset_db()

    async with SessionLocal() as db:
        with patch.object(settings, "SCHEDULER_BUFFER_SIZE", 3):
            mock_gen_svc = AsyncMock()

            # Set side effect: first date fails, other two succeed
            today = date.today()

            def side_effect(target_date):
                if target_date == today + timedelta(days=1):
                    raise GenerationOrchestratorError("Mock API error")
                return PromptChallenge(
                    publish_date=target_date,
                    prompt=f"Mock Prompt {target_date}",
                    image_url=f"/storage/mock_{target_date}.jpg",
                    target_embedding=[0.01] * 768,
                    embedding_model_name="mock-model",
                    status="scheduled",
                )

            mock_gen_svc.generate_daily_challenge.side_effect = side_effect
            scheduler = ChallengeSchedulerService(db, generation_svc=mock_gen_svc)

            generated = await scheduler.populate_buffer()
            # It should skip the failed one and successfully generate the other 2
            assert len(generated) == 2, (
                f"Expected 2 challenges generated successfully, got {len(generated)}"
            )

            # Assert calls occurred for all 3 dates
            mock_gen_svc.generate_daily_challenge.assert_any_call(today + timedelta(days=1))
            mock_gen_svc.generate_daily_challenge.assert_any_call(today + timedelta(days=2))
            mock_gen_svc.generate_daily_challenge.assert_any_call(today + timedelta(days=3))

            print(
                "✔ Scenario 3 Passed: Scheduler recovered from failure on day 1 and successfully generated days 2 and 3."
            )


async def run_scenario_4():
    """
    Scenario 4: Scheduler is executed repeatedly.
    No duplicate Daily Challenges are created.
    """
    print("\n--- Running Scenario 4: Idempotent Executions, No Duplicates ---")
    await reset_db()

    # We will use the REAL ChallengeGenerationService but mock the AIClient layer to test DB inserts
    mock_prompt = GeneratedPrompt(
        text="Real-looking mock prompt", theme="Retro", category="Obj", difficulty="easy"
    )
    mock_image = GeneratedImage(image_bytes=b"jpeg_mock_bytes")
    mock_embedding = GeneratedEmbedding(
        vector=[0.02] * 768, model_name="gemini-embedding-2", dimension=768
    )

    async with SessionLocal() as db:
        with patch.object(settings, "SCHEDULER_BUFFER_SIZE", 2):
            gen_svc = ChallengeGenerationService(db)

            # Patch actual AI client methods inside generation service
            gen_svc.prompt_svc.generate_daily_challenge_prompt = AsyncMock(return_value=mock_prompt)
            gen_svc.image_svc.generate_image = AsyncMock(return_value=mock_image)
            gen_svc.embedding_svc.generate_embedding = AsyncMock(return_value=mock_embedding)
            gen_svc.storage_svc.upload_image = AsyncMock(return_value="/storage/images/mock.jpg")

            scheduler = ChallengeSchedulerService(db, generation_svc=gen_svc)

            # Execution 1
            print("Running Execution 1...")
            gen_1 = await scheduler.populate_buffer()
            assert len(gen_1) == 2, f"Expected 2 challenges generated, got {len(gen_1)}"

            # Execution 2 (immediate rerun)
            print("Running Execution 2...")
            gen_2 = await scheduler.populate_buffer()
            assert len(gen_2) == 0, f"Expected 0 challenges generated, got {len(gen_2)}"

            # Double check database records count in DB
            stmt = select(PromptChallenge)
            res = await db.execute(stmt)
            all_records = res.scalars().all()
            assert len(all_records) == 2, (
                f"Expected exactly 2 PromptChallenge records, found {len(all_records)}"
            )

            print(
                "✔ Scenario 4 Passed: Repeated runs are fully idempotent and create no duplicates."
            )


async def run_publication_tests():
    """Verifies the transition of daily challenge status to 'published'."""
    print("\n--- Running Publication Transitions test ---")
    await reset_db()

    async with SessionLocal() as db:
        today = date.today()
        # Seed today's challenge as scheduled
        today_challenge = PromptChallenge(
            publish_date=today,
            prompt="Today's challenge prompt",
            image_url="/storage/today.jpg",
            target_embedding=[0.01] * 768,
            embedding_model_name="mock-model",
            status="scheduled",
        )
        db.add(today_challenge)
        await db.commit()

    async with SessionLocal() as db:
        scheduler = ChallengeSchedulerService(db)

        # Publish challenge
        pub_challenge = await scheduler.publish_today_challenge()
        assert pub_challenge is not None
        assert pub_challenge.status == "published"

        # Re-run publication (idempotency check)
        pub_challenge_rerun = await scheduler.publish_today_challenge()
        assert pub_challenge_rerun is not None
        assert pub_challenge_rerun.status == "published"
        assert pub_challenge_rerun.id == pub_challenge.id

        print(
            "✔ Publication tests passed: Successfully published scheduled challenge and verified idempotency."
        )


async def main():
    print("=========================================")
    print("STARTING SCHEDULER INTEGRATION TEST SUITE")
    print("=========================================")
    try:
        await run_scenario_1()
        await run_scenario_2()
        await run_scenario_3()
        await run_scenario_4()
        await run_publication_tests()
        print("\n=========================================")
        print("ALL SCHEDULER SCENARIOS VERIFIED SUCCESSFULLY")
        print("=========================================")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        os._exit(1)


if __name__ == "__main__":
    asyncio.run(main())
