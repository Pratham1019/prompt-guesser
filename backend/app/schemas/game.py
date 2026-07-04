from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GuessAttemptBase(BaseModel):
    attempt_number: int
    guess_text: str
    similarity_score: float
    evaluation_feedback: Optional[str] = None


class GuessAttemptCreate(BaseModel):
    guess_text: str = Field(..., min_length=1, max_length=1000)


class GameSessionCreate(BaseModel):
    player_id: str
    prompt_challenge_id: int


class GuessAttemptResponse(GuessAttemptBase):
    id: int
    game_session_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GameSessionResponse(BaseModel):
    id: int
    player_id: str
    prompt_challenge_id: int
    status: str
    attempts_used: int
    attempts_remaining: int
    best_score: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    is_completed: bool
    revealed_prompt: Optional[str] = None
    attempts: List[GuessAttemptResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DailyChallengePlayResponse(BaseModel):
    challenge_id: int
    image_url: str
    publish_date: date
    session: GameSessionResponse
