from fastapi import APIRouter

from app.api.v1.endpoints import gameplay

api_router = APIRouter()
api_router.include_router(gameplay.router, prefix="/gameplay", tags=["gameplay"])
