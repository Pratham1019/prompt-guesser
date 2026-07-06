from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import settings
from app.services.cron import CronService

router = APIRouter()


async def verify_cron_secret(
    authorization: Optional[str] = Header(None),
    x_cron_secret: Optional[str] = Header(None),
) -> None:
    """
    Dependency to validate cron secret authentication.
    Accepts Bearer token or custom header.
    """
    secret = settings.CRON_SECRET

    # If secret is unset or default, reject access as a precaution
    if not secret or secret == "dev-secret-key":
        # Allow default only in non-production
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cron automation is disabled in production due to unconfigured secrets.",
            )

    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_cron_secret:
        token = x_cron_secret.strip()

    if not token or token != secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials.",
        )


@router.post(
    "/cron/daily",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_cron_secret)],
)
async def trigger_daily_cron(db: AsyncSession = Depends(get_db)):
    """
    Hidden administrative endpoint to trigger the daily automation tasks.
    """
    cron_svc = CronService(db)
    report = await cron_svc.run_daily_tasks()

    if not report.get("success", False):
        error_msg = report.get("error", "Unknown error")
        if "already running" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Daily automation tasks failed: {error_msg}",
        )

    return report
