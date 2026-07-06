from fastapi import APIRouter

from app.api.v1.endpoints import gameplay, internal

api_router = APIRouter()
api_router.include_router(gameplay.router, prefix="/gameplay", tags=["gameplay"])
api_router.include_router(internal.router, prefix="/internal", include_in_schema=False)
