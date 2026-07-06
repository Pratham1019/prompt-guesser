from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PromptChallengeBase(BaseModel):
    prompt: str
    image_url: str
    status: str = "draft"
    publish_date: Optional[date] = None


class PromptChallengeCreate(PromptChallengeBase):
    pass


class PromptChallengeResponse(PromptChallengeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
