import time
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.logging import logger
from app.services.cleanup import CleanupService
from app.services.scheduler import ChallengeSchedulerService


class CronService:
    """
    Orchestrates all daily automated maintenance tasks (challenge generation,
    publication, and expired data cleanup) in a clean, idempotent manner.
    """

    _lock = False

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.scheduler = ChallengeSchedulerService(db)
        self.cleanup_svc = CleanupService(db)

    async def run_daily_tasks(self) -> Dict:
        """
        Executes the daily automated maintenance workflow.
        Returns a structured dictionary report.
        """
        if CronService._lock:
            logger.warning(
                "Cron execution aborted: another automation task is already in progress."
            )
            return {
                "success": False,
                "error": "Another automation task is already running.",
                "duration_ms": 0,
            }

        start_time = time.time()
        logger.info("Daily automation cron job execution started.")
        CronService._lock = True

        generated_count = 0
        deleted_count = 0
        today_published = False

        try:
            # 1. Publish today's challenge
            logger.info("Cron: Executing daily challenge publication...")
            published_challenge = await self.scheduler.publish_today_challenge()
            today_published = published_challenge is not None

            # 2. Maintain future challenge buffer compliance
            logger.info("Cron: Maintaining future challenge buffer...")
            generated_challenges = await self.scheduler.populate_buffer()
            generated_count = len(generated_challenges)

            # 3. Clean up expired challenges and storage files
            logger.info("Cron: Performing expired challenge and storage cleanup...")
            deleted_ids = await self.cleanup_svc.cleanup_expired_challenges()
            deleted_count = len(deleted_ids)

            duration_ms = int((time.time() - start_time) * 1000)

            # Fetch updated buffer status
            status = await self.scheduler.get_buffer_status()

            report = {
                "success": True,
                "today_published": today_published,
                "generated": generated_count,
                "deleted_images": deleted_count,
                "deleted_challenges": deleted_count,
                "future_buffer": status["active_count"],
                "duration_ms": duration_ms,
            }

            logger.info(f"Daily automation cron finished successfully. Report: {report}")
            return report

        except Exception as e:
            await self.db.rollback()
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Daily automation cron job failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms,
            }
        finally:
            CronService._lock = False
