from app.config import settings
from app.services.evaluation.base import BaseEvaluationService, EvaluationResult
from app.services.evaluation.providers.gemini import GeminiEvaluationService
from app.services.evaluation.providers.jaccard import JaccardEvaluationService


def get_evaluation_service() -> BaseEvaluationService:
    """
    Factory function to resolve the configured semantic evaluation service.
    Avoids hardcoding concrete evaluator choices in application controllers.
    """
    eval_type = settings.AI_EVALUATOR_TYPE.lower()
    if eval_type == "gemini":
        return GeminiEvaluationService()
    elif eval_type == "jaccard":
        return JaccardEvaluationService()
    else:
        raise ValueError(f"Unknown evaluator type: {settings.AI_EVALUATOR_TYPE}")


__all__ = [
    "BaseEvaluationService",
    "EvaluationResult",
    "JaccardEvaluationService",
    "GeminiEvaluationService",
    "get_evaluation_service",
]
