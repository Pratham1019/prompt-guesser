from app.services.evaluation.base import BaseEvaluationService, EvaluationResult


class JaccardEvaluationService(BaseEvaluationService):
    """
    Temporary Jaccard similarity evaluation service to satisfy the gameplay engine requirements
    without performing real vector embedding or LLM judge calculations.
    """

    async def evaluate(self, guess: str, target: str) -> EvaluationResult:
        guess_clean = guess.strip().lower()
        target_clean = target.strip().lower()

        if guess_clean == target_clean:
            return EvaluationResult(score=100.0, feedback="EXACT MATCH!")

        guess_words = set(guess_clean.split())
        target_words = set(target_clean.split())
        if not guess_words or not target_words:
            return EvaluationResult(score=0.0, feedback="NO MATCHING WORDS")

        intersection = guess_words.intersection(target_words)
        union = guess_words.union(target_words)
        score = float(len(intersection) / len(union) * 100.0)
        score = round(score, 2)

        feedback = f"MATCHED {len(intersection)} OUT OF {len(union)} UNIQUE WORDS"
        return EvaluationResult(score=score, feedback=feedback)
