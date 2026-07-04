from app.config import settings
from app.logging import logger
from app.services.ai.client import AIClient
from app.services.ai.exceptions import EmbeddingGenerationError
from app.services.ai.schemas import GeneratedEmbedding


class EmbeddingGeneratorService:
    """
    Generates embeddings for prompt texts using the configured AI embedding model.
    """

    def __init__(self, client: AIClient) -> None:
        self.client = client
        self.model_name = settings.AI_EMBEDDING_MODEL
        self.expected_dimension = 768  # Assuming dimension for the Daily Challenge DB schema

    async def generate_embedding(self, text: str) -> GeneratedEmbedding:
        """
        Generates and validates an embedding for the provided text.
        """
        try:
            vector = await self.client.generate_embedding(text)

            # Validate dimensions
            if len(vector) != self.expected_dimension:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.expected_dimension}, got {len(vector)}"
                )
                # We could pad/truncate or raise. Let's raise to be strict.
                raise EmbeddingGenerationError(
                    f"Embedding dimension mismatch. Expected {self.expected_dimension}, got {len(vector)}."
                )

            return GeneratedEmbedding(
                vector=vector, model_name=self.model_name, dimension=len(vector)
            )
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingGenerationError(f"Embedding generation failed: {e}") from e
