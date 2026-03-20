import time

from core.database.connection import create_tables, execute, fetch_one, get_user_items
from core.services.alchemy_service import brew_pill
from core.services.quests_service import today_str
from core.services.resource_conversion_service import convert_resources
from core.services.settlement import settle_enhance, settle_quest_claim, settle_quest_claim_all
from tests.conftest import create_user


def _insert_in_progress(request_id: str, user_id: str, action: str, now: int) -> None:
    execute(
        "INSERT INTO request_dedup (request_id, user_id, action, created_at, response_json) VALUES (%s, %s, %s, %s, NULL)",
        (request_id, user_id, action, now),
    )


def test_settle_quest_claim_request_in_progress_returns_409(test_db):
    create_user("u1", "甲")
    now = int(time.time())
    _insert_in_progress("RID-QC-1", "u1", "quest_claim", now)

    payload, status = settle_quest_claim(
        user_id="u1",
        quest_id="daily_signin",
        request_id="RID-QC-1",
        claim_cooldown_seconds=0,
        today=today_str(),
        now=now,
    )
    assert status == 409
    assert payload.get("code") == "REQUEST_IN_PROGRESS"

    row = fetch_one("SELECT stamina, copper FROM users WHERE user_id = %s", ("u1",))
    assert int(row["stamina"]) == 24
    assert int(row["copper"]) == 1000


def test_settle_quest_claim_all_request_in_progress_returns_409(test_db):
    create_user("u1", "甲")
    now = int(time.time())
    _insert_in_progress("RID-QCA-1", "u1", "quest_claim_all", now)

    payload, status = settle_quest_claim_all(
        user_id="u1",
        request_id="RID-QCA-1",
        claim_cooldown_seconds=0,
        today=today_str(),
        now=now,
    )
    assert status == 409
    assert payload.get("code") == "REQUEST_IN_PROGRESS"

    row = fetch_one("SELECT stamina, copper FROM users WHERE user_id = %s", ("u1",))
    assert int(row["stamina"]) == 24
    assert int(row["copper"]) == 1000


def test_settle_enhance_request_in_progress_returns_409(test_db):
    create_user("u1", "甲")
    now = int(time.time())
    _insert_in_progress("RID-ENH-1", "u1", "enhance", now)

    payload, status = settle_enhance(
        user_id="u1",
        item_db_id=99999,
        request_id="RID-ENH-1",
        enhance_cooldown_seconds=0,
        now=now,
    )
    assert status == 409
    assert payload.get("code") == "REQUEST_IN_PROGRESS"

    row = fetch_one("SELECT stamina, copper FROM users WHERE user_id = %s", ("u1",))
    assert int(row["stamina"]) == 24
    assert int(row["copper"]) == 1000


def test_alchemy_brew_request_in_progress_returns_409(test_db):
    create_user("u1", "甲")
    now = int(time.time())
    _insert_in_progress("RID-ALC-1", "u1", "alchemy_brew", now)

    payload, status = brew_pill("u1", "any_recipe", request_id="RID-ALC-1")
    assert status == 409
    assert payload.get("code") == "REQUEST_IN_PROGRESS"

    row = fetch_one("SELECT stamina, copper FROM users WHERE user_id = %s", ("u1",))
    assert int(row["stamina"]) == 24
    assert int(row["copper"]) == 1000


def test_resource_convert_request_in_progress_returns_409(test_db):
    create_user("u1", "甲")
    now = int(time.time())
    _insert_in_progress("RID-RC-1", "u1", "resource_convert", now)

    payload, status = convert_resources(
        user_id="u1",
        target_item_id="iron_ore",
        quantity=1,
        route="steady",
        request_id="RID-RC-1",
    )
    assert status == 409
    assert payload.get("code") == "REQUEST_IN_PROGRESS"

    row = fetch_one("SELECT stamina, copper FROM users WHERE user_id = %s", ("u1",))
    assert int(row["stamina"]) == 24
    assert int(row["copper"]) == 1000


def test_create_tables_dedupes_duplicate_user_keys_and_restores_unique_indexes(test_db):
    conn = test_db
    with conn.cursor() as cur:
        cur.execute("DROP INDEX IF EXISTS idx_users_username_unique")
        cur.execute("DROP INDEX IF EXISTS idx_users_telegram_id_unique")
    conn.commit()

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (user_id, in_game_username, created_at, telegram_id) VALUES (%s, %s, %s, %s)",
            ("dup_u1", "重复名", 100, "tg_dup"),
        )
        cur.execute(
            "INSERT INTO users (user_id, in_game_username, created_at, telegram_id) VALUES (%s, %s, %s, %s)",
            ("dup_u2", "重复名", 200, "tg_dup"),
        )
    conn.commit()

    create_tables(conn)

    row_a = fetch_one(
        "SELECT in_game_username, telegram_id FROM users WHERE user_id = %s",
        ("dup_u1",),
    )
    row_b = fetch_one(
        "SELECT in_game_username, telegram_id FROM users WHERE user_id = %s",
        ("dup_u2",),
    )
    assert row_a is not None and row_b is not None
    assert row_a["in_game_username"] != row_b["in_game_username"]
    assert [row_a["telegram_id"], row_b["telegram_id"]].count("tg_dup") == 1
    assert [row_a["telegram_id"], row_b["telegram_id"]].count("") == 1

    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = %s",
            ("idx_users_username_unique",),
        )
        username_index = cur.fetchone()
        cur.execute(
            "SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = %s",
            ("idx_users_telegram_id_unique",),
        )
        telegram_index = cur.fetchone()
    assert username_index is not None
    assert telegram_index is not None


def test_get_user_items_returns_newest_first(test_db):
    create_user("u1", "甲")
    execute(
        """INSERT INTO items (user_id, item_id, item_name, item_type, quality, quantity, level,
           attack_bonus, defense_bonus, hp_bonus, mp_bonus,
           first_round_reduction_pct, crit_heal_pct, element_damage_pct, low_hp_shield_pct)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("u1", "old_item", "旧物品", "material", "common", 1, 1, 0, 0, 0, 0, 0, 0, 0, 0),
    )
    execute(
        """INSERT INTO items (user_id, item_id, item_name, item_type, quality, quantity, level,
           attack_bonus, defense_bonus, hp_bonus, mp_bonus,
           first_round_reduction_pct, crit_heal_pct, element_damage_pct, low_hp_shield_pct)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("u1", "new_item", "新物品", "material", "common", 1, 1, 0, 0, 0, 0, 0, 0, 0, 0),
    )
    items = get_user_items("u1")
    assert items
    assert items[0].get("item_id") == "new_item"
