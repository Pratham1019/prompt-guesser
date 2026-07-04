from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.logging import logger
from app.models.challenge import PromptChallenge
from app.models.game import GameSession
from app.schemas.game import (
    DailyChallengePlayResponse,
    GameSessionResponse,
    GuessAttemptCreate,
    GuessAttemptResponse,
)
from app.services.gameplay import (
    ChallengeNotFoundError,
    GameplayError,
    GameplayService,
    InvalidGuessError,
    MaxAttemptsExceededError,
    SessionAlreadyCompletedError,
)

router = APIRouter()


def get_player_id(
    x_player_id: Optional[str] = Header(None, alias="X-Player-ID"),
    player_id: Optional[str] = Query(None),
) -> str:
    """
    FastAPI dependency that extracts the player identifier.
    Accepts 'X-Player-ID' header or 'player_id' query parameter.
    """
    pid = x_player_id or player_id
    if not pid:
        raise HTTPException(
            status_code=400,
            detail="Missing player identifier. Please provide 'X-Player-ID' header or 'player_id' query param.",
        )
    return pid


def map_session_to_schema(session: GameSession, challenge: PromptChallenge) -> GameSessionResponse:
    """
    Maps game database models to GameSessionResponse schema, enforcing privacy
    by revealing the original challenge prompt only after session completion.
    """
    is_completed = session.status == "completed"
    attempts_remaining = max(0, 5 - session.attempts_used)
    revealed_prompt = challenge.prompt if is_completed else None

    attempts_resp = [
        GuessAttemptResponse(
            id=att.id,
            game_session_id=att.game_session_id,
            attempt_number=att.attempt_number,
            guess_text=att.guess_text,
            similarity_score=att.similarity_score,
            evaluation_feedback=att.evaluation_feedback,
            created_at=att.created_at,
        )
        for att in session.attempts
    ]

    return GameSessionResponse(
        id=session.id,
        player_id=session.player_id,
        prompt_challenge_id=session.prompt_challenge_id,
        status=session.status,
        attempts_used=session.attempts_used,
        attempts_remaining=attempts_remaining,
        best_score=session.best_score,
        created_at=session.created_at,
        completed_at=session.completed_at,
        is_completed=is_completed,
        revealed_prompt=revealed_prompt,
        attempts=attempts_resp,
    )


@router.get("/today", response_model=DailyChallengePlayResponse)
async def get_today_challenge(
    player_id: str = Depends(get_player_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves today's Daily Challenge details (excluding private fields)
    along with the player's active session state and attempts history.
    """
    gameplay_svc = GameplayService(db)
    try:
        challenge = await gameplay_svc.get_today_challenge()
        session = await gameplay_svc.get_or_create_game_session(player_id, challenge.id)

        session_schema = map_session_to_schema(session, challenge)

        return DailyChallengePlayResponse(
            challenge_id=challenge.id,
            image_url=challenge.image_url or "",
            publish_date=challenge.publish_date or gameplay_svc.get_local_today(),
            session=session_schema,
        )
    except ChallengeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to fetch today's challenge: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching daily challenge."
        ) from e


@router.post("/guess", response_model=GameSessionResponse)
async def submit_guess(
    guess_in: GuessAttemptCreate,
    player_id: str = Depends(get_player_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a guess text for today's daily challenge.
    Calculates similarity, records the attempt, checks completions,
    and returns the updated game state.
    """
    gameplay_svc = GameplayService(db)
    try:
        # Retrieve today's challenge to ensure player is guessing the active one
        challenge = await gameplay_svc.get_today_challenge()

        # Submit the guess
        session = await gameplay_svc.submit_guess(player_id, challenge.id, guess_in.guess_text)

        # Map to response schema
        return map_session_to_schema(session, challenge)

    except ChallengeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (
        SessionAlreadyCompletedError,
        MaxAttemptsExceededError,
        InvalidGuessError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except GameplayError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unhandled exception in guess submission endpoint: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during guess validation."
        ) from e
