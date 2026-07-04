from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.config import settings
from app.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events using lifespan context.
    """
    logger.info(
        "Starting application server...",
        extra={"project_name": settings.PROJECT_NAME, "environment": settings.ENVIRONMENT},
    )
    yield
    logger.info("Shutting down application server...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A neo-brutalist prompt-guessing game where players decode AI image prompts.",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS configuration
if settings.CORS_ORIGINS:
    logger.info("Configuring CORS origins", extra={"allowed_origins": settings.CORS_ORIGINS})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register health check route directly to root `/health`
app.include_router(health_router)

# Register v1 API endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)
