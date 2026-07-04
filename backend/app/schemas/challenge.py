from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PromptChallengeBase(BaseModel):
    prompt: str
    image_url: str
    status: str = "draft"
    publish_date: Optional[date] = None
    embedding_model_name: str


class PromptChallengeCreate(PromptChallengeBase):
    target_embedding: List[float]


class PromptChallengeResponse(PromptChallengeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
