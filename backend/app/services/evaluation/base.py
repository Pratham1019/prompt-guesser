from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel


class EvaluationResult(BaseModel):
    """
    Structured response representing the output of a guess evaluation.
    """

    score: float
    feedback: Optional[str] = None
    matched_concepts: list[str] = []
    missing_concepts: list[str] = []
    reasoning: str = ""
    confidence_score: float = 1.0


class BaseEvaluationService(ABC):
    """
    Clean interface abstracting the evaluation engine from the gameplay loop.
    """

    @abstractmethod
    async def evaluate(self, guess: str, target: str) -> EvaluationResult:
        """
        Compares a player's guess against the target challenge prompt.
        Returns a structured EvaluationResult (score from 0.0 to 100.0).
        """
        pass
