import time
import zoneinfo
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logging import logger
from app.models.challenge import PromptChallenge
from app.services.generation import ChallengeGenerationService


class ChallengeSchedulerService:
    """
    Manages future challenge buffer compliance, schedules publication,
    and runs clean automated operations.
    """

    def __init__(
        self,
        db: AsyncSession,
        generation_svc: Optional[ChallengeGenerationService] = None,
    ) -> None:
        self.db = db
        self.generation_svc = generation_svc or ChallengeGenerationService(db)
        self.timezone = zoneinfo.ZoneInfo(settings.SCHEDULER_TIMEZONE)
        self.buffer_size = settings.SCHEDULER_BUFFER_SIZE

    def get_local_today(self) -> date:
        """Returns today's date in the configured timezone."""
        return datetime.now(self.timezone).date()

    async def get_buffer_status(self) -> Dict:
        """
        Inspects the database and returns details about current future challenges.
        Future challenges are those scheduled for dates strictly after today.
        """
        today = self.get_local_today()
        tomorrow = today + timedelta(days=1)
        end_date = today + timedelta(days=self.buffer_size)

        # Query all challenges in the publish window
        stmt = select(PromptChallenge).where(
            PromptChallenge.publish_date >= tomorrow,
            PromptChallenge.publish_date <= end_date,
        )
        result = await self.db.execute(stmt)
        challenges = result.scalars().all()

        challenge_map = {c.publish_date: c for c in challenges}

        active_dates: List[date] = []
        failed_dates: List[date] = []
        missing_dates: List[date] = []

        for i in range(1, self.buffer_size + 1):
            check_date = today + timedelta(days=i)
            c = challenge_map.get(check_date)
            if c is None:
                missing_dates.append(check_date)
            elif c.status == "failed":
                failed_dates.append(check_date)
            else:
                active_dates.append(check_date)

        return {
            "today": today,
            "configured_buffer": self.buffer_size,
            "active_count": len(active_dates),
            "failed_count": len(failed_dates),
            "missing_count": len(missing_dates),
            "active_dates": active_dates,
            "failed_dates": failed_dates,
            "missing_dates": missing_dates,
        }

    async def populate_buffer(self) -> List[PromptChallenge]:
        """
        Generates challenges for any missing or failed dates in the buffer window.
        Logs status at start, buffer size, generated dates, and elapsed duration.
        """
        if not settings.SCHEDULER_ENABLED:
            logger.info("Scheduler execution skipped: SCHEDULER_ENABLED is set to False.")
            return []

        start_time = time.time()
        logger.info("Scheduler buffer check initiated.")

        # Self-healing: Reset any stuck "generating" challenges back to "failed"
        # so they can be identified as missing/failed and regenerated.
        from sqlalchemy import update

        await self.db.execute(
            update(PromptChallenge)
            .where(PromptChallenge.status == "generating")
            .values(status="failed")
        )
        await self.db.commit()

        status = await self.get_buffer_status()
        logger.info(
            f"Current buffer status - Configured: {self.buffer_size}, "
            f"Unpublished Active: {status['active_count']}, Missing: {status['missing_count']}, Failed: {status['failed_count']}"
        )

        generated_challenges: List[PromptChallenge] = []

        # Combine missing and failed dates to restore buffer sequentially
        dates_to_generate = sorted(status["missing_dates"] + status["failed_dates"])

        for target_date in dates_to_generate:
            logger.info(f"Attempting challenge generation for date: {target_date}")
            try:
                challenge = await self.generation_svc.generate_daily_challenge(target_date)
                generated_challenges.append(challenge)
            except Exception as e:
                # Log failure and safely proceed to next date
                logger.error(
                    f"Failed to generate challenge for {target_date}: {e}. "
                    "Skipping and continuing to build remaining buffer."
                )

        duration = time.time() - start_time
        logger.info(
            f"Scheduler buffer execution completed in {duration:.2f}s. "
            f"Successfully generated {len(generated_challenges)} challenges."
        )

        return generated_challenges

    async def publish_today_challenge(self) -> Optional[PromptChallenge]:
        """
        Locates the challenge scheduled for today's local date (or the most recent scheduled date in the past,
        to recover from service outages) and transitions its status to 'published'.
        Idempotent (running repeatedly returns the already published challenge).
        Missed historical scheduled challenges are transitioned to 'archived'.
        """
        today = self.get_local_today()
        logger.info(f"Publish event triggered. Checking challenges up to: {today}")

        # 1. Check if there is already a published challenge for today
        stmt_pub = select(PromptChallenge).where(
            PromptChallenge.publish_date == today,
            PromptChallenge.status == "published",
        )
        pub_res = await self.db.execute(stmt_pub)
        already_published = pub_res.scalar_one_or_none()

        # 2. Query all scheduled challenges for today or earlier
        stmt = (
            select(PromptChallenge)
            .where(
                PromptChallenge.publish_date <= today,
                PromptChallenge.status == "scheduled",
            )
            .order_by(PromptChallenge.publish_date.desc())
        )
        result = await self.db.execute(stmt)
        scheduled_challenges = list(result.scalars().all())

        if already_published is not None:
            logger.info(f"Challenge for today ({today}) is already published.")
            # If any past scheduled challenges exist, archive them because we already have a published challenge
            if scheduled_challenges:
                for missed_challenge in scheduled_challenges:
                    missed_challenge.status = "archived"
                    logger.warning(
                        f"Archiving missed scheduled challenge ID {missed_challenge.id} "
                        f"for past date {missed_challenge.publish_date} because today's challenge is already published."
                    )
                await self.db.commit()
            return already_published

        if not scheduled_challenges:
            logger.warning(
                f"No scheduled challenge found in the database for today or earlier dates up to {today}"
            )
            return None

        # Publish the most recent scheduled challenge (first in the list)
        challenge_to_publish = scheduled_challenges[0]
        challenge_to_publish.status = "published"
        logger.info(
            f"Publishing challenge ID {challenge_to_publish.id} for scheduled date {challenge_to_publish.publish_date}."
        )

        # Archive any older scheduled challenges that were missed
        for missed_challenge in scheduled_challenges[1:]:
            missed_challenge.status = "archived"
            logger.warning(
                f"Archiving missed scheduled challenge ID {missed_challenge.id} "
                f"for past date {missed_challenge.publish_date} due to scheduler downtime."
            )

        await self.db.commit()
        await self.db.refresh(challenge_to_publish)
        return challenge_to_publish

    async def run_cleanup(self) -> List[int]:
        """
        Runs the cleanup service task to remove expired daily challenges
        and their associated storage objects from cloud bucket.
        """
        from app.services.cleanup import CleanupService

        cleanup_svc = CleanupService(self.db)
        return await cleanup_svc.cleanup_expired_challenges()
