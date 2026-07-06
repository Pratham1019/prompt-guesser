import asyncio
import os
import sys
from datetime import date

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import SessionLocal, engine
from app.main import app
from app.models.base import Base
from app.models.challenge import PromptChallenge
from app.models.game import GameSession


async def reset_db():
    """Drops and recreates all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed_today_challenge(prompt: str) -> int:
    """Seeds today's daily challenge in the database."""
    async with SessionLocal() as db:
        challenge = PromptChallenge(
            prompt=prompt,
            image_url="/storage/images/test_astronaut.jpg",
            status="published",
            publish_date=date.today(),
        )
        db.add(challenge)
        await db.commit()
        await db.refresh(challenge)
        return challenge.id


async def test_scenario_1(client: AsyncClient, challenge_id: int):
    """
    Scenario 1: Player opens today's challenge for the first time.
    """
    print("\n--- Running Scenario 1: First-time Access ---")
    headers = {"X-Player-ID": "player_1"}

    response = await client.get("/api/v1/gameplay/today", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data["challenge_id"] == challenge_id
    assert data["image_url"] == "/storage/images/test_astronaut.jpg"
    assert data["publish_date"] == date.today().isoformat()

    session = data["session"]
    assert session["status"] == "active"
    assert session["attempts_used"] == 0
    assert session["attempts_remaining"] == 5
    assert session["best_score"] == 0.0
    assert session["is_completed"] is False
    assert session["revealed_prompt"] is None
    assert len(session["attempts"]) == 0

    print("[OK] Scenario 1 Passed: Initial session state is clean and prompt is hidden.")


async def test_scenario_2(client: AsyncClient):
    """
    Scenario 2: Player submits five guesses without reaching 100%.
    Challenge completes correctly.
    """
    print("\n--- Running Scenario 2: 5 Failed Guesses ---")
    headers = {"X-Player-ID": "player_2"}

    # Retrieve challenge first to create session
    await client.get("/api/v1/gameplay/today", headers=headers)

    guesses = ["cat", "dog", "car", "house", "rocket"]

    for i, guess in enumerate(guesses):
        response = await client.post(
            "/api/v1/gameplay/guess", headers=headers, json={"guess_text": guess}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["attempts_used"] == i + 1
        assert data["attempts_remaining"] == 5 - (i + 1)

        if i < 4:
            assert data["status"] == "active"
            assert data["is_completed"] is False
            assert data["revealed_prompt"] is None
        else:
            # 5th attempt should mark session as completed and reveal prompt
            assert data["status"] == "completed"
            assert data["is_completed"] is True
            assert data["revealed_prompt"] == "A tiny astronaut fishing from Saturn's rings"
            assert len(data["attempts"]) == 5

    # Double check by calling GET today again
    get_res = await client.get("/api/v1/gameplay/today", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["session"]["status"] == "completed"
    assert get_data["session"]["revealed_prompt"] == "A tiny astronaut fishing from Saturn's rings"

    print("[OK] Scenario 2 Passed: Completed after 5 attempts and prompt revealed.")


async def test_scenario_3(client: AsyncClient):
    """
    Scenario 3: Player reaches 100% before the fifth attempt.
    Challenge ends immediately.
    """
    print("\n--- Running Scenario 3: Exact Match (100%) ---")
    headers = {"X-Player-ID": "player_3"}

    # Attempt 1: partial match
    res_1 = await client.post(
        "/api/v1/gameplay/guess", headers=headers, json={"guess_text": "tiny astronaut"}
    )
    assert res_1.status_code == 200
    data_1 = res_1.json()
    assert data_1["status"] == "active"
    assert data_1["is_completed"] is False
    assert data_1["revealed_prompt"] is None

    # Attempt 2: exact match
    res_2 = await client.post(
        "/api/v1/gameplay/guess",
        headers=headers,
        json={"guess_text": "A tiny astronaut fishing from Saturn's rings"},
    )
    assert res_2.status_code == 200
    data_2 = res_2.json()
    assert data_2["attempts_used"] == 2
    assert data_2["best_score"] == 100.0
    assert data_2["status"] == "completed"
    assert data_2["is_completed"] is True
    assert data_2["revealed_prompt"] == "A tiny astronaut fishing from Saturn's rings"

    print("[OK] Scenario 3 Passed: Completed instantly on exact match.")


async def test_scenario_4(client: AsyncClient):
    """
    Scenario 4: Player attempts a 6th submission.
    The request is rejected.
    """
    print("\n--- Running Scenario 4: Reject 6th Submission ---")
    headers = {"X-Player-ID": "player_2"}  # player_2 already used 5 attempts in Scenario 2

    response = await client.post(
        "/api/v1/gameplay/guess", headers=headers, json={"guess_text": "sixth_guess"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "guesses rejected" in data["detail"].lower() or "limit reached" in data["detail"].lower()

    print("[OK] Scenario 4 Passed: 6th guess was successfully rejected with HTTP 400.")


async def test_scenario_5(client: AsyncClient):
    """
    Scenario 5: Player revisits today's challenge after completion.
    Completed results are returned instead of an active challenge.
    """
    print("\n--- Running Scenario 5: Re-visiting Completed Challenge ---")
    headers = {"X-Player-ID": "player_3"}  # player_3 completed on 2nd attempt in Scenario 3

    response = await client.get("/api/v1/gameplay/today", headers=headers)
    assert response.status_code == 200
    data = response.json()

    session = data["session"]
    assert session["status"] == "completed"
    assert session["is_completed"] is True
    assert session["revealed_prompt"] == "A tiny astronaut fishing from Saturn's rings"
    assert len(session["attempts"]) == 2

    print("[OK] Scenario 5 Passed: Completed state returned correctly.")


async def test_scenario_6(client: AsyncClient):
    """
    Scenario 6: Application restart.
    Gameplay state remains intact.
    """
    print("\n--- Running Scenario 6: Database Persistence Check ---")

    # We will close the connection and open a new session check directly
    async with SessionLocal() as db:
        stmt = select(GameSession).where(GameSession.player_id == "player_3")
        res = await db.execute(stmt)
        session = res.scalar_one()
        assert session.status == "completed"
        assert session.attempts_used == 2
        assert session.best_score == 100.0

    print("[OK] Scenario 6 Passed: Gameplay session state is verified in the DB.")


async def test_validation_errors(client: AsyncClient):
    """Verifies edge case validations."""
    print("\n--- Running Validation Errors Tests ---")

    # Validation 1: Missing Player ID
    res_err1 = await client.get("/api/v1/gameplay/today")
    assert res_err1.status_code == 400
    assert "missing player identifier" in res_err1.json()["detail"].lower()

    # Validation 2: Empty Guess Text
    headers = {"X-Player-ID": "player_4"}
    res_err2 = await client.post(
        "/api/v1/gameplay/guess", headers=headers, json={"guess_text": "   "}
    )
    assert res_err2.status_code == 400
    assert "empty" in res_err2.json()["detail"].lower()

    print("[OK] Validation error handling passes correctly.")


async def main():
    print("=========================================")
    print("STARTING GAMEPLAY ENGINE INTEGRATION TEST")
    print("=========================================")
    await reset_db()

    challenge_id = await seed_today_challenge(prompt="A tiny astronaut fishing from Saturn's rings")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        try:
            await test_scenario_1(client, challenge_id)
            await test_scenario_2(client)
            await test_scenario_3(client)
            await test_scenario_4(client)
            await test_scenario_5(client)
            await test_scenario_6(client)
            await test_validation_errors(client)
            print("\n=========================================")
            print("ALL GAMEPLAY SCENARIOS VERIFIED SUCCESSFULLY")
            print("=========================================")
        except Exception as e:
            print(f"\n[ERROR] Test suite failed: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
