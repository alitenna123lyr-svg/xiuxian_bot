from concurrent.futures import ThreadPoolExecutor
import time

import pytest
from flask import Flask

from core.database.connection import fetch_one, execute
from tests.conftest import create_user

TEST_INTERNAL_TOKEN = "unit-test-internal-token"


@pytest.fixture()
def internal_token_env(test_db, monkeypatch):
    monkeypatch.setenv("XXBOT_INTERNAL_API_TOKEN", TEST_INTERNAL_TOKEN)
    from core.config import config
    config.reload()
    yield

    monkeypatch.delenv("XXBOT_INTERNAL_API_TOKEN", raising=False)
    config.reload()


def test_internal_token_validation(internal_token_env):
    from core.server import is_internal_request_authorized

    assert is_internal_request_authorized("") is False
    assert is_internal_request_authorized("wrong-token") is False
    assert is_internal_request_authorized(TEST_INTERNAL_TOKEN) is True


def test_skill_learn_concurrent_single_success(test_db):
    from core.routes.skills import skill_learn

    create_user("u1", "甲", rank=5)
    app = Flask(__name__)

    def _learn_once():
        with app.test_request_context(
            "/api/skills/learn",
            method="POST",
            json={"user_id": "u1", "skill_id": "stone_skin"},
            headers={"X-Actor-User-Id": "u1"},
        ):
            resp = skill_learn()
            if isinstance(resp, tuple):
                response_obj, status = resp
                return status, response_obj.get_json() or {}
            return resp.status_code, resp.get_json() or {}

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda _: _learn_once(), range(4)))

    success_count = sum(1 for status, payload in results if status == 200 and payload.get("success"))
    assert success_count == 1

    user = fetch_one("SELECT copper FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 600

    row = fetch_one(
        "SELECT COUNT(1) AS c FROM user_skills WHERE user_id = %s AND skill_id = %s",
        ("u1", "stone_skin"),
    )
    assert int(row["c"]) == 1


def test_achievement_claim_concurrent_single_reward(test_db):
    from core.services.achievements_service import claim_achievement

    create_user("u1", "甲", rank=7)

    with ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(lambda _: claim_achievement("u1", "rank_7"), range(5)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    assert success_count == 5

    user = fetch_one("SELECT copper, exp FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1300
    assert int(user["exp"]) == 1200

    row = fetch_one(
        "SELECT COUNT(1) AS c FROM user_achievements WHERE user_id = %s AND achievement_id = %s AND claimed = 1",
        ("u1", "rank_7"),
    )
    assert int(row["c"]) == 1


def test_event_claim_concurrent_single_reward(test_db):
    from core.services.events_service import claim_event_reward

    create_user("u1", "甲", rank=7)

    with ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(lambda _: claim_event_reward("u1", "spring_festival"), range(5)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    assert success_count == 1

    user = fetch_one("SELECT copper, exp FROM users WHERE user_id = %s", ("u1",))
    assert int(user["copper"]) == 1320
    assert int(user["exp"]) == 1150

    row = fetch_one(
        "SELECT claims FROM event_claims WHERE user_id = %s AND event_id = %s",
        ("u1", "spring_festival"),
    )
    assert row is not None
    assert int(row["claims"]) == 1


def test_event_exchange_concurrent_respects_limit_and_points(test_db):
    from core.database.connection import fetch_one as _fetch_one
    from core.services.events_service import get_active_events, exchange_event_points

    create_user("u1", "甲", rank=8)
    active = get_active_events()
    assert active
    chosen_event = next(
        (
            e
            for e in active
            if any(int((x or {}).get("limit", 0) or 0) == 1 for x in (e.get("exchange_shop") or []))
        ),
        None,
    )
    if not chosen_event:
        pytest.skip("No active exchange entry with weekly limit=1")
    exchange = next(x for x in (chosen_event.get("exchange_shop") or []) if int((x or {}).get("limit", 0) or 0) == 1)
    event_id = str(chosen_event.get("id"))
    exchange_id = str(exchange.get("id"))
    cost = int(exchange.get("cost_points", 0) or 0)
    execute(
        """
        INSERT INTO event_points(user_id, event_id, points_total, points_spent, updated_at)
        VALUES(%s, %s, %s, 0, %s)
        ON CONFLICT(user_id, event_id)
        DO UPDATE SET points_total = excluded.points_total, points_spent = 0, updated_at = excluded.updated_at
        """,
        ("u1", event_id, max(cost * 10, 1000), int(time.time())),
    )

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda _: exchange_event_points("u1", event_id, exchange_id, quantity=1), range(4)))

    success_count = sum(1 for payload, status in results if status == 200 and payload.get("success"))
    assert success_count == 1
    for payload, status in results:
        if status == 200:
            continue
        assert payload.get("code") in {"LIMIT", "INSUFFICIENT_POINTS"}

    row = _fetch_one(
        """
        SELECT quantity FROM event_exchange_claims
        WHERE user_id = %s AND event_id = %s AND exchange_id = %s
        ORDER BY id DESC LIMIT 1
        """,
        ("u1", event_id, exchange_id),
    )
    assert row is not None
    assert int(row["quantity"] or 0) == 1

    points_row = _fetch_one(
        "SELECT points_total, points_spent FROM event_points WHERE user_id = %s AND event_id = %s",
        ("u1", event_id),
    )
    assert points_row is not None
    assert int(points_row["points_spent"] or 0) == cost


def test_world_boss_concurrent_single_kill(test_db, monkeypatch):
    from core.services.events_service import get_world_boss_status, attack_world_boss
    from core.services.events_service import _world_boss as _world_boss_cfg

    create_user("u1", "甲", rank=12)
    create_user("u2", "乙", rank=12)
    now = int(time.time())
    execute("UPDATE users SET stamina = 24, stamina_updated_at = %s WHERE user_id IN (%s, %s)", (now, "u1", "u2"))

    # Ensure state exists then force low hp to make kill race deterministic.
    status = get_world_boss_status()
    assert status.get("success") is True
    boss_id = str((_world_boss_cfg() or {}).get("id") or "world_boss_1")
    execute("UPDATE world_boss_state SET hp = 1, last_reset = %s WHERE boss_id = %s", (now, boss_id))

    monkeypatch.setattr("core.services.events_service.random.uniform", lambda a, b: 1.0)
    monkeypatch.setattr("core.services.events_service.random.random", lambda: 1.0)

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(lambda uid: attack_world_boss(uid), ("u1", "u2")))

    success_results = [(payload, status_code) for payload, status_code in results if status_code == 200 and payload.get("success")]
    fail_results = [(payload, status_code) for payload, status_code in results if not (status_code == 200 and payload.get("success"))]
    assert len(success_results) == 1
    assert success_results[0][0].get("defeated") is True
    assert len(fail_results) == 1
    assert fail_results[0][0].get("code") == "DEFEATED"
