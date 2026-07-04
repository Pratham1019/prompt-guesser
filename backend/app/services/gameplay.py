import zoneinfo
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.logging import logger
from app.models.challenge import PromptChallenge
from app.models.game import GameSession, GuessAttempt
from app.services.evaluation import BaseEvaluationService, JaccardEvaluationService


class GameplayError(Exception):
    """Base exception for gameplay engine errors."""

    pass


class ChallengeNotFoundError(GameplayError):
    """Raised when no active daily challenge is published for the request date."""

    pass


class SessionAlreadyCompletedError(GameplayError):
    """Raised when attempting to submit a guess to an already finished game session."""

    pass


class MaxAttemptsExceededError(GameplayError):
    """Raised when attempting to guess after utilizing all 5 attempts."""

    pass


class InvalidGuessError(GameplayError):
    """Raised for malformed or empty guess text submissions."""

    pass


class GameplayService:
    """
    Core engine running the daily challenge gameplay loop.
    Enforces rules, persists progress, isolates session transactions,
    and returns response-ready states.
    """

    def __init__(
        self,
        db: AsyncSession,
        evaluation_svc: Optional[BaseEvaluationService] = None,
    ) -> None:
        self.db = db
        self.evaluation_svc = evaluation_svc or JaccardEvaluationService()
        self.timezone = zoneinfo.ZoneInfo(settings.SCHEDULER_TIMEZONE)

    def get_local_today(self) -> date:
        """Returns today's date in the configured timezone."""
        return datetime.now(self.timezone).date()

    async def get_today_challenge(self) -> PromptChallenge:
        """
        Retrieves today's active challenge.
        Raises ChallengeNotFoundError if no challenge is published for today.
        """
        today = self.get_local_today()
        logger.info(f"Querying active challenge for local date: {today}")

        stmt = select(PromptChallenge).where(
            PromptChallenge.publish_date == today,
            PromptChallenge.status == "published",
        )
        result = await self.db.execute(stmt)
        challenge = result.scalar_one_or_none()

        if challenge is None:
            logger.warning(f"No published daily challenge found for date: {today}")
            raise ChallengeNotFoundError(f"No daily challenge is available for {today}.")

        return challenge

    async def get_or_create_game_session(self, player_id: str, challenge_id: int) -> GameSession:
        """
        Retrieves a player's game session for a specific challenge.
        Creates it if it does not yet exist.
        """
        # Load session along with its related attempts in order
        stmt = (
            select(GameSession)
            .where(
                GameSession.player_id == player_id,
                GameSession.prompt_challenge_id == challenge_id,
            )
            .options(selectinload(GameSession.attempts))
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            logger.info(
                f"Creating new active game session for player {player_id} on challenge {challenge_id}."
            )
            session = GameSession(
                player_id=player_id,
                prompt_challenge_id=challenge_id,
                status="active",
                attempts_used=0,
                best_score=0.0,
            )
            self.db.add(session)
            await self.db.commit()

            # Re-fetch to ensure relationship loading works correctly
            result = await self.db.execute(stmt)
            session = result.scalar_one()

        return session

    async def submit_guess(self, player_id: str, challenge_id: int, guess_text: str) -> GameSession:
        """
        Submits a player's guess attempt.
        Validates gameplay rules, evaluates similarity, creates GuessAttempt,
        updates session status, and commits updates atomically.
        """
        guess_clean = guess_text.strip()
        if not guess_clean:
            raise InvalidGuessError("Guess text cannot be empty.")

        # 1. Fetch prompt challenge
        stmt_challenge = select(PromptChallenge).where(PromptChallenge.id == challenge_id)
        res_challenge = await self.db.execute(stmt_challenge)
        challenge = res_challenge.scalar_one_or_none()

        if challenge is None:
            raise ChallengeNotFoundError(f"Challenge ID {challenge_id} not found.")

        # 2. Get player's game session
        session = await self.get_or_create_game_session(player_id, challenge_id)

        # 3. Enforce gameplay rules
        if session.status != "active":
            raise SessionAlreadyCompletedError(
                f"Session is already completed (status: '{session.status}'). Additional guesses rejected."
            )

        if session.attempts_used >= 5:
            raise MaxAttemptsExceededError(
                "Maximum attempt limit (5) reached. Additional guesses rejected."
            )

        attempt_number = session.attempts_used + 1
        logger.info(
            f"Player {player_id} submitting attempt #{attempt_number} for challenge {challenge_id}."
        )
        try:
            if not challenge.prompt:
                raise ChallengeNotFoundError(
                    f"Challenge ID {challenge_id} is missing its generated prompt text."
                )

            # 4. Invoke the evaluation abstraction
            logger.info(
                f"Evaluating guess: '{guess_clean[:50]}...' against target challenge ID {challenge_id}"
            )
            eval_result = await self.evaluation_svc.evaluate(guess_clean, challenge.prompt)

            # 5. Create GuessAttempt record
            attempt = GuessAttempt(
                game_session_id=session.id,
                attempt_number=attempt_number,
                guess_text=guess_clean,
                similarity_score=eval_result.score,
                evaluation_feedback=eval_result.feedback,
            )
            session.attempts.append(attempt)

            # 6. Update Game Session aggregates
            session.attempts_used = attempt_number
            session.best_score = max(session.best_score, eval_result.score)

            # 7. Check completion conditions (100% score or 5 attempts used)
            if eval_result.score == 100.0 or attempt_number == 5:
                session.status = "completed"
                session.completed_at = datetime.now(timezone.utc)
                logger.info(
                    f"Game session ID {session.id} completed (attempts: {attempt_number}, best score: {session.best_score}%)."
                )

            # 8. Commit database updates atomically
            await self.db.commit()

            # Reload session with selectinload(GameSession.attempts) to ensure attempts are populated
            stmt_reload = (
                select(GameSession)
                .where(GameSession.id == session.id)
                .options(selectinload(GameSession.attempts))
            )
            reload_res = await self.db.execute(stmt_reload)
            session = reload_res.scalar_one()

            return session

        except Exception as e:
            # Atomic safety: rollback the session on any failure (database or evaluation)
            await self.db.rollback()
            logger.error(f"Guess submission transaction aborted for player {player_id} due to: {e}")
            if isinstance(e, GameplayError):
                raise
            raise GameplayError(
                f"Failed to submit guess due to internal service failure: {e}"
            ) from e
