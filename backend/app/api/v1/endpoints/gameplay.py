from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import settings
from app.logging import logger
from app.models.challenge import PromptChallenge
from app.models.game import GameSession
from app.schemas.game import (
    DailyChallengePlayResponse,
    GameSessionResponse,
    GuessAttemptCreate,
    GuessAttemptResponse,
)
from app.services.evaluation import BaseEvaluationService, get_evaluation_service
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
    evaluation_svc: BaseEvaluationService = Depends(get_evaluation_service),
):
    """
    Retrieves today's Daily Challenge details (excluding private fields)
    along with the player's active session state and attempts history.
    """
    gameplay_svc = GameplayService(db, evaluation_svc=evaluation_svc)
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
    evaluation_svc: BaseEvaluationService = Depends(get_evaluation_service),
):
    """
    Submits a guess text for today's daily challenge.
    Calculates similarity, records the attempt, checks completions,
    and returns the updated game state.
    """
    gameplay_svc = GameplayService(db, evaluation_svc=evaluation_svc)
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


class ChallengeDebugOverride(BaseModel):
    prompt: str
    image_url: Optional[str] = None


@router.post("/debug/override-challenge")
async def override_challenge(payload: ChallengeDebugOverride, db: AsyncSession = Depends(get_db)):
    """
    Developer override endpoint. Allows changing today's target prompt and
    image URL for local manual testing.
    Disabled in production.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403, detail="Debug operations are disabled in production environment."
        )

    from sqlalchemy import select

    from app.models.challenge import PromptChallenge

    today = date.today()
    stmt = select(PromptChallenge).where(PromptChallenge.publish_date == today)
    result = await db.execute(stmt)
    challenge = result.scalar_one_or_none()

    from app.services.ai.client import AIClient
    from app.services.ai.image_generator import ImageGeneratorService
    from app.services.storage import StorageService

    image_status = "success"

    try:
        ai_client = AIClient()
    except Exception as conf_err:
        ai_client = None
        image_status = f"skipped: {conf_err}"

    # 1. Generate and upload image matching the new prompt

    # 2. Generate and upload image matching the new prompt
    image_url = payload.image_url
    storage_path = None
    if not image_url:
        if ai_client:
            try:
                image_svc = ImageGeneratorService(ai_client)
                storage_svc = StorageService()
                image_data = await image_svc.generate_image(payload.prompt)
                image_url = await storage_svc.upload_image(
                    image_data.image_bytes, target_date=today
                )
                storage_path = storage_svc.get_storage_path(today)
            except Exception as e:
                logger.warning(
                    f"Could not generate image for debug override: {e}. Falling back to dynamic mock placeholder image."
                )
                image_status = f"failed: {e} (using Picsum Photos fallback)"
                try:
                    import httpx

                    async with httpx.AsyncClient() as client:
                        resp = await client.get(
                            "https://picsum.photos/600/450", follow_redirects=True
                        )
                        if resp.status_code == 200:
                            storage_svc = StorageService()
                            image_url = await storage_svc.upload_image(
                                resp.content, target_date=today
                            )
                            storage_path = storage_svc.get_storage_path(today)
                        else:
                            image_url = "/storage/images/test_astronaut.jpg"
                except Exception as fetch_err:
                    logger.error(f"Failed to fetch mock placeholder image: {fetch_err}")
                    image_url = "/storage/images/test_astronaut.jpg"
        else:
            image_url = "/storage/images/test_astronaut.jpg"

    if not challenge:
        # Create a new one
        challenge = PromptChallenge(
            prompt=payload.prompt,
            image_url=image_url,
            storage_path=storage_path,
            status="published",
            publish_date=today,
        )
        db.add(challenge)
    else:
        challenge.prompt = payload.prompt
        challenge.image_url = image_url
        challenge.storage_path = storage_path

    await db.commit()
    await db.refresh(challenge)

    # Optional: Delete all game sessions for this challenge to force a clean reset for all players
    # so they can test the new prompt from attempt 1.
    from app.models.game import GameSession

    del_stmt = delete(GameSession).where(GameSession.prompt_challenge_id == challenge.id)
    await db.execute(del_stmt)
    await db.commit()

    return {
        "message": "Challenge updated successfully. All active sessions reset.",
        "challenge_id": challenge.id,
        "image_url": challenge.image_url,
        "debug_info": {
            "image_generation": image_status,
        },
    }
