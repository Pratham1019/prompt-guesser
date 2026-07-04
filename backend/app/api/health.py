from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import settings
from app.logging import logger
from app.schemas.health import HealthCheckSchema

router = APIRouter()


@router.get("/health", response_model=HealthCheckSchema)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify backend application status and database connectivity.
    """
    try:
        # Verify database connectivity by running a basic SELECT query
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "environment": settings.ENVIRONMENT,
                "database": "unhealthy",
            },
        )

    return HealthCheckSchema(
        status="healthy",
        environment=settings.ENVIRONMENT,
        database="healthy",
    )
