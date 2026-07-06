import time
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logging import logger
from app.models.challenge import PromptChallenge
from app.models.game import GameSession
from app.services.storage import StorageService


class CleanupService:
    """
    Dedicated service for identifying and deleting expired daily challenges,
    cleaning up their associated storage files and database records.
    """

    def __init__(self, db: AsyncSession, storage_svc: Optional[StorageService] = None) -> None:
        self.db = db
        self.storage_svc = storage_svc or StorageService()
        self.retention_days = getattr(settings, "SCHEDULER_RETENTION_DAYS", 30)

    async def cleanup_expired_challenges(self) -> List[int]:
        """
        Identifies challenges older than retention_days, deletes their images from local storage,
        and deletes their database records (along with associated game sessions).
        """
        cutoff_date = date.today() - timedelta(days=self.retention_days)
        logger.info(
            f"Starting expired challenge cleanup. Cutoff date: {cutoff_date} (Retention: {self.retention_days} days)"
        )
        start_time = time.time()

        # Query all challenges published before cutoff date
        stmt = select(PromptChallenge).where(
            PromptChallenge.publish_date < cutoff_date,
            PromptChallenge.status == "published",
        )
        result = await self.db.execute(stmt)
        expired_challenges = list(result.scalars().all())

        if not expired_challenges:
            logger.info("No expired challenges found for cleanup.")
            return []

        logger.info(f"Found {len(expired_challenges)} expired challenges to delete.")
        deleted_ids: List[int] = []

        for challenge in expired_challenges:
            logger.info(f"Cleaning up challenge ID {challenge.id} (Date: {challenge.publish_date})")

            # 1. Delete associated storage object
            if challenge.storage_path:
                try:
                    await self.storage_svc.delete_image(challenge.storage_path)
                except Exception as e:
                    # Log but continue so database records can still be cleaned
                    # and deleting an already deleted object is idempotent
                    logger.error(
                        f"Failed to delete storage object {challenge.storage_path} for challenge {challenge.id}: {e}. "
                        "Continuing database cleanup."
                    )

            # 2. Delete database records
            try:
                # Delete sessions first to satisfy RESTRICT foreign key constraint on prompt_challenge_id
                session_del_stmt = delete(GameSession).where(
                    GameSession.prompt_challenge_id == challenge.id
                )
                await self.db.execute(session_del_stmt)

                # Delete challenge
                await self.db.delete(challenge)
                await self.db.commit()

                deleted_ids.append(challenge.id)
                logger.info(
                    f"Successfully deleted expired challenge ID {challenge.id} from database."
                )
            except Exception as db_err:
                await self.db.rollback()
                logger.error(
                    f"Failed to delete database record for challenge ID {challenge.id}: {db_err}"
                )

        duration = time.time() - start_time
        logger.info(
            f"Expired challenge cleanup completed in {duration:.2f}s. Successfully cleaned {len(deleted_ids)} challenges."
        )
        return deleted_ids
