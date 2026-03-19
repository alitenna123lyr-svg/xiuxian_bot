import time

from core.database.connection import execute
from core.services.bounty_service import publish_bounty, accept_bounty, submit_bounty


def _create_user(user_id: str, *, copper: int = 0) -> None:
    execute(
        "INSERT INTO users (user_id, in_game_username, rank, element, created_at, exp, copper, gold) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, f"U_{user_id}", 10, "火", int(time.time()), 1000, copper, 0),
    )


def _grant_item(user_id: str, item_id: str, quantity: int) -> None:
    execute(
        """
        INSERT INTO items (user_id, item_id, item_name, item_type, quality, quantity, level,
                          attack_bonus, defense_bonus, hp_bonus, mp_bonus,
                          first_round_reduction_pct, crit_heal_pct, element_damage_pct, low_hp_shield_pct)
        VALUES (%s, %s, %s, %s, 'common', %s, 1, 0, 0, 0, 0, 0, 0, 0, 0)
        """,
        (user_id, item_id, item_id, "material", int(quantity)),
    )


def test_bounty_publish_accept_submit_flow(test_db):
    _create_user("bounty_poster", copper=100)
    _create_user("bounty_worker", copper=0)
    _grant_item("bounty_worker", "herb", 10)

    pub, st = publish_bounty(
        user_id="bounty_poster",
        wanted_item_id="herb",
        wanted_quantity=5,
        reward_spirit_low=6,
        description="测试悬赏",
    )
    assert st == 200 and pub.get("success")
    bounty_id = int(pub["bounty_id"])

    acc, acc_st = accept_bounty(user_id="bounty_worker", bounty_id=bounty_id)
    assert acc_st == 200 and acc.get("success")

    sub, sub_st = submit_bounty(user_id="bounty_worker", bounty_id=bounty_id)
    assert sub_st == 200 and sub.get("success")
