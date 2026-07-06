import time
from datetime import date
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging import logger
from app.models.challenge import PromptChallenge
from app.services.ai.client import AIClient
from app.services.ai.image_generator import ImageGeneratorService
from app.services.ai.prompt_generator import PromptGeneratorService
from app.services.storage import StorageService


class GenerationOrchestratorError(Exception):
    """Raised when the overall generation pipeline fails."""

    pass


class ChallengeGenerationService:
    """
    Orchestrates the entire Daily Challenge content generation pipeline.
    Invokes prompt, image, and embedding services, uploads assets, and persists to the database.
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_client: Optional[AIClient] = None,
        prompt_svc: Optional[PromptGeneratorService] = None,
        image_svc: Optional[ImageGeneratorService] = None,
        storage_svc: Optional[StorageService] = None,
    ) -> None:
        self.db = db
        self.ai_client = ai_client or AIClient()
        self.prompt_svc = prompt_svc or PromptGeneratorService(self.ai_client)
        self.image_svc = image_svc or ImageGeneratorService(self.ai_client)
        self.storage_svc = storage_svc or StorageService()

    async def generate_daily_challenge(self, target_date: date) -> PromptChallenge:
        """
        Executes the full pipeline for a specific date:
        1. Checks for existing challenge for the date
        2. Inserts a 'generating' placeholder (or sets failed to generating atomically) to lock the date
        3. Generates Prompt, Image, and Embedding
        4. Uploads Image
        5. Updates and transitions status to 'scheduled'
        6. On failure, transitions status to 'failed' and cleans up orphaned files
        """
        logger.info(f"Starting Challenge Generation Pipeline for date: {target_date}")
        start_time = time.time()
        image_url: Optional[str] = None

        # 1. Check existing challenge
        stmt = select(PromptChallenge).where(PromptChallenge.publish_date == target_date)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            if existing.status in ("generating", "scheduled", "published"):
                raise GenerationOrchestratorError(
                    f"A challenge with status '{existing.status}' already exists for {target_date}."
                )

            # Use atomic compare-and-swap update to acquire lock on failed date
            stmt_update = (
                update(PromptChallenge)
                .where(PromptChallenge.id == existing.id, PromptChallenge.status == "failed")
                .values(status="generating")
            )
            upd_res = await self.db.execute(stmt_update)
            if getattr(upd_res, "rowcount", 0) == 0:
                raise GenerationOrchestratorError(
                    f"Conflict: Another worker is already regenerating the failed challenge for {target_date}."
                )
            challenge = existing
        else:
            # Create a 'generating' placeholder to lock the publish_date
            challenge = PromptChallenge(
                publish_date=target_date,
                status="generating",
            )
            self.db.add(challenge)

        # Commit/flush to reserve the publish_date and lock state
        try:
            await self.db.commit()
            await self.db.refresh(challenge)
        except Exception as e:
            await self.db.rollback()
            raise GenerationOrchestratorError(
                f"Failed to reserve date {target_date} for generation: {e}"
            ) from e

        # Run the generation pipeline
        try:
            # 2. Generate Prompt
            prompt_start = time.time()
            prompt_data = await self.prompt_svc.generate_daily_challenge_prompt(target_date)
            logger.info(
                "Prompt generated successfully", extra={"duration": time.time() - prompt_start}
            )

            # 3. Generate Image
            image_start = time.time()
            image_data = await self.image_svc.generate_image(prompt_data.text)
            logger.info(
                "Image generated successfully", extra={"duration": time.time() - image_start}
            )

            # 4. Upload Image
            upload_start = time.time()
            image_url = await self.storage_svc.upload_image(
                image_data.image_bytes, target_date=target_date
            )
            storage_path = self.storage_svc.get_storage_path(target_date)
            logger.info(
                "Image uploaded successfully",
                extra={
                    "duration": time.time() - upload_start,
                    "url": image_url,
                    "path": storage_path,
                },
            )

            # 5. Finalize Challenge
            db_start = time.time()
            challenge.prompt = prompt_data.text
            challenge.image_url = image_url
            challenge.storage_path = storage_path
            challenge.status = "scheduled"

            await self.db.commit()
            await self.db.refresh(challenge)

            logger.info(
                "Challenge finalized and scheduled successfully",
                extra={"duration": time.time() - db_start, "id": challenge.id},
            )

            total_time = time.time() - start_time
            logger.info(
                f"Challenge Generation Pipeline completed successfully in {total_time:.2f}s"
            )
            return challenge

        except Exception as e:
            logger.error(f"Generation failure for date {target_date}: {e}")

            # Explicit rollback on the failed transaction
            await self.db.rollback()

            # Clean up uploaded image if it was written to storage
            if image_url is not None:
                try:
                    await self.storage_svc.delete_image(image_url)
                except Exception as cleanup_err:
                    logger.error(f"Failed to delete orphaned image: {cleanup_err}")

            try:
                # Transition status to failed via a direct update query
                stmt_failed = (
                    update(PromptChallenge)
                    .where(PromptChallenge.publish_date == target_date)
                    .values(status="failed")
                )
                await self.db.execute(stmt_failed)
                await self.db.commit()
                logger.info(f"Transitioned challenge for date {target_date} to 'failed'.")
            except Exception as db_err:
                await self.db.rollback()
                logger.error(f"Failed to transition challenge to failed status: {db_err}")

            raise GenerationOrchestratorError(f"Challenge generation pipeline failed: {e}") from e

    async def regenerate_failed_challenge(self, challenge_id: int) -> PromptChallenge:
        """
        Regenerates a challenge that previously failed.
        """
        stmt = select(PromptChallenge).where(PromptChallenge.id == challenge_id)
        result = await self.db.execute(stmt)
        challenge = result.scalar_one_or_none()

        if challenge is None:
            raise GenerationOrchestratorError(f"Challenge ID {challenge_id} not found.")

        if challenge.status != "failed":
            raise GenerationOrchestratorError(
                f"Challenge ID {challenge_id} is not in 'failed' status (current status: '{challenge.status}')."
            )
        logger.info(
            f"Regenerating failed challenge ID: {challenge_id} (scheduled for {challenge.publish_date})"
        )
        image_url: Optional[str] = None

        # Use compare-and-swap update to acquire lock atomically
        stmt_update = (
            update(PromptChallenge)
            .where(PromptChallenge.id == challenge_id, PromptChallenge.status == "failed")
            .values(status="generating")
        )
        upd_res = await self.db.execute(stmt_update)
        if getattr(upd_res, "rowcount", 0) == 0:
            raise GenerationOrchestratorError(
                f"Conflict: Another worker has already claimed or updated failed challenge ID {challenge_id}."
            )

        # Re-fetch the updated object
        stmt_refetch = select(PromptChallenge).where(PromptChallenge.id == challenge_id)
        res = await self.db.execute(stmt_refetch)
        challenge = res.scalar_one()

        await self.db.commit()
        await self.db.refresh(challenge)

        # Run pipeline
        try:
            target_date_val = challenge.publish_date or date.today()
            prompt_data = await self.prompt_svc.generate_daily_challenge_prompt(target_date_val)
            image_data = await self.image_svc.generate_image(prompt_data.text)
            image_url = await self.storage_svc.upload_image(
                image_data.image_bytes, target_date=target_date_val
            )
            storage_path = self.storage_svc.get_storage_path(target_date_val)

            challenge.prompt = prompt_data.text
            challenge.image_url = image_url
            challenge.storage_path = storage_path
            challenge.status = "scheduled"

            await self.db.commit()
            await self.db.refresh(challenge)
            logger.info(f"Challenge ID {challenge_id} regenerated and scheduled successfully.")
            return challenge
        except Exception as e:
            logger.error(f"Regeneration failure for challenge ID {challenge_id}: {e}")
            await self.db.rollback()

            # Clean up uploaded image if it was written to storage
            if image_url is not None:
                try:
                    await self.storage_svc.delete_image(image_url)
                except Exception as cleanup_err:
                    logger.error(f"Failed to delete orphaned image: {cleanup_err}")

            try:
                stmt_failed = (
                    update(PromptChallenge)
                    .where(PromptChallenge.id == challenge_id)
                    .values(status="failed")
                )
                await self.db.execute(stmt_failed)
                await self.db.commit()
            except Exception as db_err:
                await self.db.rollback()
                logger.error(f"Failed to transition challenge back to failed status: {db_err}")

            raise GenerationOrchestratorError(f"Failed to regenerate challenge: {e}") from e
