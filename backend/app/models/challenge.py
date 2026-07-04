from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Date, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator, UserDefinedType

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.game import GameSession


class PostgresVector(UserDefinedType):
    """
    A custom type that compiles directly to VECTOR(dim) in PostgreSQL,
    avoiding python pgvector library import errors on migration runners.
    """

    def __init__(self, dim: int):
        self.dim = dim

    def get_col_spec(self, **kw):
        return f"VECTOR({self.dim})"


class SafeVector(TypeDecorator):
    """
    A dialect-agnostic type that compiles to VECTOR(dim) on PostgreSQL
    and falls back to standard JSON on SQLite for local development.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresVector(self.dim))
        return dialect.type_descriptor(JSON())

    def __repr__(self):
        return f"SafeVector(dim={self.dim})"


class PromptChallenge(Base):
    """
    Represents the target prompt, AI-generated image, and embedding vector
    used to calculate similarity scores.
    """

    __tablename__ = "prompt_challenges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Lifecycle and scheduling for Daily Challenges
    # status can be: draft, generating, scheduled, published, archived, failed
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True, nullable=False)
    publish_date: Mapped[Optional[date]] = mapped_column(
        Date, unique=True, index=True, nullable=True
    )

    # Embedding-related fields for semantic scoring (using SafeVector)
    target_embedding: Mapped[Optional[List[float]]] = mapped_column(SafeVector(768), nullable=True)
    # Embedding model name metadata (e.g., "text-embedding-004")
    embedding_model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

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
