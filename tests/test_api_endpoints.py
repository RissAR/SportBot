"""Automated test suite verifying SportBot REST API endpoints, HMAC-SHA256, and business rules."""

import asyncio
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.app import app
from src.config import settings
from src.db.seed import seed_initial_data
from src.db.session import init_db


def generate_valid_tma_init_data(bot_token: str, telegram_id: int, username: str) -> str:
    """Generate cryptographically valid Telegram initData query string for testing."""
    auth_date = int(time.time())
    user_payload = json.dumps(
        {"id": telegram_id, "first_name": "Athlete", "username": username},
        separators=(",", ":"),
    )
    params = {
        "auth_date": str(auth_date),
        "query_id": "AAHDemoQueryId123",
        "user": user_payload,
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    signature = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    params["hash"] = signature
    return urllib.parse.urlencode(params)


async def run_all_tests() -> None:
    """Execute end-to-end acceptance tests against the FastAPI application."""
    print(">>> 1. Initializing database and seed data...")
    await init_db()
    await seed_initial_data()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Test 1: Health check
        print(">>> 2. Testing /health...")
        res = await client.get("/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert res.json() == {"status": "ok"}

        # Test 2: Security check: unauthenticated request when DEBUG=False returns 401
        print(">>> 3. Testing security: unauthorized access with DEBUG=False...")
        original_debug = settings.DEBUG
        try:
            settings.DEBUG = False
            res = await client.get("/api/user/me")
            assert res.status_code == 401, f"Expected 401 Unauthorized, got {res.status_code}"
            assert "detail" in res.json()
        finally:
            settings.DEBUG = original_debug

        # Test 3: Authenticated user via valid Telegram HMAC-SHA256 initData
        print(">>> 4. Testing HMAC-SHA256 signature validation...")
        test_bot_token = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
        original_token = settings.BOT_TOKEN
        settings.BOT_TOKEN = test_bot_token

        test_tg_id = 777123456
        test_username = "test_calisthenics_pro"
        valid_init_data = generate_valid_tma_init_data(test_bot_token, test_tg_id, test_username)

        auth_headers = {"Authorization": f"tma {valid_init_data}"}

        # Test invalid signature fails
        invalid_headers = {"Authorization": f"tma {valid_init_data}&hash=fakehash123"}
        res_invalid = await client.get("/api/user/me", headers=invalid_headers)
        assert res_invalid.status_code == 401, f"Expected 401 for tampered hash, got {res_invalid.status_code}"

        # JIT User Provisioning: First access creates user
        print(">>> 5. Testing JIT user provisioning via /api/user/me...")
        res_me = await client.get("/api/user/me", headers=auth_headers)
        assert res_me.status_code == 200, f"Expected 200, got {res_me.status_code}: {res_me.text}"
        profile = res_me.json()
        assert profile["telegram_id"] == test_tg_id
        assert profile["username"] == test_username
        assert profile["current_day"] == 1
        assert profile["current_cycle"] == 1
        assert profile["difficulty_mode"] == "medium"
        assert profile["total_workouts_completed"] == 0

        # Test 4: Update difficulty mode
        print(">>> 6. Testing /api/user/difficulty...")
        res_diff = await client.patch(
            "/api/user/difficulty",
            headers=auth_headers,
            json={"difficulty_mode": "hard"},
        )
        assert res_diff.status_code == 200
        assert res_diff.json()["difficulty_mode"] == "hard"

        # Test 5: Get Today Workout (Day 1 - Push Block)
        print(">>> 7. Testing /api/cycle/today (Day 1 protocol)...")
        res_today = await client.get("/api/cycle/today", headers=auth_headers)
        assert res_today.status_code == 200, f"Error: {res_today.text}"
        today_data = res_today.json()
        assert today_data["day_number"] == 1
        assert today_data["block_type"] == "A_PUSH"
        assert today_data["is_rest_day"] is False
        assert len(today_data["warmup_steps"]) == 5, f"Expected 5 warmup steps, got {len(today_data['warmup_steps'])}"
        assert len(today_data["cooldown_steps"]) == 4, f"Expected 4 cooldown steps, got {len(today_data['cooldown_steps'])}"
        assert len(today_data["exercises"]) == 3, f"Expected 3 push exercises, got {len(today_data['exercises'])}"
        # Check that 'hard' progression was applied
        assert today_data["exercises"][0]["slug"] == "dips"
        exercise_ids = [ex["id"] for ex in today_data["exercises"]]

        # Test 6: Cycle Days Overview
        print(">>> 8. Testing /api/cycle/days overview...")
        res_days = await client.get("/api/cycle/days", headers=auth_headers)
        assert res_days.status_code == 200
        days_overview = res_days.json()
        assert len(days_overview["days"]) == 30
        assert days_overview["days"][0]["status"] == "current"  # Day 1
        assert days_overview["days"][1]["status"] == "locked"   # Day 2

        # Test 7: Complete workout for Day 1
        print(">>> 9. Testing /api/workout/complete for current day (Day 1)...")
        workout_payload = {
            "day_number": 1,
            "cycle_number": 1,
            "duration_seconds": 2100,
            "difficulty_mode": "hard",
            "exercises": [
                {
                    "exercise_id": exercise_ids[0],
                    "sets_completed": 4,
                    "value_completed": 16,
                    "is_completed": True,
                },
                {
                    "exercise_id": exercise_ids[1],
                    "sets_completed": 4,
                    "value_completed": 18,
                    "is_completed": True,
                },
                {
                    "exercise_id": exercise_ids[2],
                    "sets_completed": 4,
                    "value_completed": 12,
                    "is_completed": True,
                },
            ],
        }
        res_comp = await client.post(
            "/api/workout/complete",
            headers=auth_headers,
            json=workout_payload,
        )
        assert res_comp.status_code == 200, f"Expected 200, got {res_comp.status_code}: {res_comp.text}"
        comp_data = res_comp.json()
        assert comp_data["success"] is True
        assert comp_data["next_day"] == 2
        assert comp_data["cycle_completed"] is False

        # Verify athlete advanced to Day 2
        res_me_updated = await client.get("/api/user/me", headers=auth_headers)
        assert res_me_updated.json()["current_day"] == 2
        assert res_me_updated.json()["total_workouts_completed"] == 1

        # Test 8: Attempting to complete Day 1 again must return 400 Bad Request
        print(">>> 10. Testing rule: completing past/already completed Day 1 must return 400...")
        res_repeat = await client.post(
            "/api/workout/complete",
            headers=auth_headers,
            json=workout_payload,  # Still day_number=1
        )
        assert res_repeat.status_code == 400, f"Expected 400 Bad Request, got {res_repeat.status_code}"
        assert "Only the current day workout can be completed" in res_repeat.json()["detail"]

        # Test 9: Logging bodyweight
        print(">>> 11. Testing /api/weight logging and history...")
        res_weight = await client.post(
            "/api/weight",
            headers=auth_headers,
            json={"weight_kg": 84.5, "cycle_number": 1},
        )
        assert res_weight.status_code == 200, f"Weight error: {res_weight.text}"
        weight_data = res_weight.json()
        assert weight_data["weight_kg"] == 84.5
        assert weight_data["cycle_number"] == 1
        assert weight_data["is_cycle_reset"] is False

        # Check history
        res_history = await client.get("/api/weight/history", headers=auth_headers)
        assert res_history.status_code == 200
        history_list = res_history.json()["history"]
        assert len(history_list) >= 1
        assert history_list[-1]["weight_kg"] == 84.5

        # Test 10: Admin metrics endpoint authorization
        print(">>> 12. Testing /api/admin/metrics authorization...")
        # Non-admin user gets 403 Forbidden
        res_admin_denied = await client.get("/api/admin/metrics", headers=auth_headers)
        assert res_admin_denied.status_code == 403, f"Expected 403, got {res_admin_denied.status_code}"

        # Configure user as admin
        settings.ADMIN_IDS = str(test_tg_id)
        res_admin_ok = await client.get("/api/admin/metrics", headers=auth_headers)
        assert res_admin_ok.status_code == 200, f"Expected 200 for admin, got {res_admin_ok.status_code}"
        metrics = res_admin_ok.json()
        assert metrics["total_athletes"] >= 1
        assert metrics["total_workouts_completed"] >= 1
        assert "hard" in metrics["difficulty_distribution"]

        # Restore original settings
        settings.BOT_TOKEN = original_token
        settings.ADMIN_IDS = ""

    print("======================================================")
    print("ALL API ENDPOINT ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
    print("======================================================")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
