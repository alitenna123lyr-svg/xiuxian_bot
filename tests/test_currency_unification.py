import time

from core.database.connection import execute
from core.services.currency_service import get_currency_overview, exchange_currency


def _create_user(user_id: str, *, rank: int = 1, copper: int = 0, gold: int = 0) -> None:
    execute(
        """
        INSERT INTO users (user_id, in_game_username, rank, element, created_at, exp, copper, gold)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, f"U_{user_id}", rank, "火", int(time.time()), 1000, copper, gold),
    )


def test_currency_overview_reports_unified_wallet_and_rules(test_db):
    _create_user("currency_u1", rank=12, copper=2345, gold=7)
    resp, status = get_currency_overview("currency_u1")
    assert status == 200
    assert resp.get("success") is True
    wallet = resp.get("wallet") or {}
    assert int(wallet.get("spirit_low", 0)) == 2345
    assert int(wallet.get("spirit_mid", 0)) == 7
    assert int(resp.get("rules", {}).get("spirit_mid_equals_low", 0)) == 1000


def test_exchange_currency_applies_1000_to_1_rule(test_db):
    _create_user("currency_u2", rank=15, copper=5600, gold=2)

    up_resp, up_status = exchange_currency(user_id="currency_u2", from_currency="copper", amount=2500)
    assert up_status == 200
    assert up_resp.get("success") is True
    assert int(up_resp.get("spent", 0)) == 2000
    assert int(up_resp.get("gained", 0)) == 2
    wallet = up_resp.get("wallet") or {}
    assert int(wallet.get("spirit_low", 0)) == 3600
    assert int(wallet.get("spirit_mid", 0)) == 4

    down_resp, down_status = exchange_currency(user_id="currency_u2", from_currency="gold", amount=1)
    assert down_status == 200
    assert down_resp.get("success") is True
    wallet2 = down_resp.get("wallet") or {}
    assert int(wallet2.get("spirit_low", 0)) == 4600
    assert int(wallet2.get("spirit_mid", 0)) == 3
