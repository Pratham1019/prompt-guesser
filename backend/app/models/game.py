from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.challenge import PromptChallenge


class GameSession(Base):
    """
    Represents a player's playthrough of a Daily Challenge.
    Stores aggregated state across multiple guess attempts (max 5).
    """

    __tablename__ = "game_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name="valid_session_status",
        ),
        CheckConstraint(
            "attempts_used <= 5",
            name="max_attempts_constraint",
        ),
        UniqueConstraint(
            "player_id",
            "prompt_challenge_id",
            name="uq_game_session_player_challenge",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    prompt_challenge_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("prompt_challenges.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        index=True,
        nullable=False,
    )  # active, completed, abandoned

    attempts_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    best_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    prompt_challenge: Mapped["PromptChallenge"] = relationship(
        "PromptChallenge",
        back_populates="sessions",
    )
    attempts: Mapped[List["GuessAttempt"]] = relationship(
        "GuessAttempt",
        back_populates="game_session",
        cascade="all, delete-orphan",
        order_by="GuessAttempt.attempt_number",
    )


class GuessAttempt(Base):
    """
    Represents an individual guess attempt within a game session.
    A session can have up to 5 attempts.
    """

    __tablename__ = "guess_attempts"
    __table_args__ = (
        UniqueConstraint(
            "game_session_id",
            "attempt_number",
            name="uq_guess_attempt_session_number",
        ),
        CheckConstraint(
            "attempt_number BETWEEN 1 AND 5",
            name="valid_attempt_number",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    game_session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    guess_text: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    similarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Optional field for LLM judge feedback
    evaluation_feedback: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    game_session: Mapped["GameSession"] = relationship(
        "GameSession",
        back_populates="attempts",
    )
