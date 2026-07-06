from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Date, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.game import GameSession


class SafeVector(TypeDecorator):
    """
    Legacy compatibility type wrapper representing a vector.
    Retained to allow older Alembic migrations to run successfully.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSON())


class PromptChallenge(Base):
    """
    Represents the target prompt and the AI-generated image used in daily challenges.
    """

    __tablename__ = "prompt_challenges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Lifecycle and scheduling for Daily Challenges
    # status can be: draft, generating, scheduled, published, archived, failed
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True, nullable=False)
    publish_date: Mapped[Optional[date]] = mapped_column(
        Date, unique=True, index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    sessions: Mapped[List["GameSession"]] = relationship(
        "GameSession",
        back_populates="prompt_challenge",
    )
