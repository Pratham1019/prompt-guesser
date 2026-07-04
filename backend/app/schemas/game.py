from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class GuessAttemptBase(BaseModel):
    attempt_number: int
    guess_text: str
    similarity_score: float
    evaluation_feedback: Optional[str] = None


class GuessAttemptCreate(BaseModel):
    guess_text: str


class GuessAttemptResponse(GuessAttemptBase):
    id: int
    game_session_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GameSessionBase(BaseModel):
    prompt_challenge_id: int
    status: str = "active"
    attempts_used: int = 0
    best_score: float = 0.0


class GameSessionCreate(BaseModel):
    prompt_challenge_id: int


class GameSessionResponse(GameSessionBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    attempts: List[GuessAttemptResponse] = []

    model_config = ConfigDict(from_attributes=True)
