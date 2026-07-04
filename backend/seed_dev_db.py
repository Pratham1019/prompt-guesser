import asyncio
import os
import sys
from datetime import date

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models.base import Base
from app.models.challenge import PromptChallenge


async def seed():
    # Make sure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        from sqlalchemy import select

        stmt = select(PromptChallenge).where(PromptChallenge.publish_date == date.today())
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        target_prompt = (
            "A tiny astronaut fishing from Saturn's rings at golden hour, "
            "cinematic lighting, ultra-detailed digital illustration, "
            "vibrant pastel color palette, whimsical, highly detailed background."
        )

        if existing:
            print(
                f"Challenge for today ({date.today()}) already exists in the database. Updating prompt and image."
            )
            existing.prompt = target_prompt
            existing.image_url = "/storage/images/test_astronaut.jpg"
            existing.status = "published"
            await db.commit()
            print("Successfully updated today's challenge!")
            return

        challenge = PromptChallenge(
            prompt=target_prompt,
            image_url="/storage/images/test_astronaut.jpg",
            target_embedding=[0.01] * 768,
            embedding_model_name="mock-model",
            status="published",
            publish_date=date.today(),
        )
        db.add(challenge)
        await db.commit()
        print(f"Successfully seeded today's challenge with ID: {challenge.id}")


if __name__ == "__main__":
    asyncio.run(seed())
