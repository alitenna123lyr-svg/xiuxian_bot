from core.services import settlement_extra


def _mock_user():
    return {
        "user_id": "u1",
        "rank": 1,
        "copper": 0,
        "gold": 0,
    }


def test_shop_buy_allows_quantity_100(monkeypatch):
    monkeypatch.setattr(settlement_extra, "get_user_by_id", lambda _uid: _mock_user())
    monkeypatch.setattr(
        settlement_extra,
        "can_buy_item",
        lambda *args, **kwargs: (False, "copper", "余额不足"),
    )

    payload, status = settlement_extra.settle_shop_buy(
        user_id="u1",
        item_id="hp_pill",
        quantity=100,
    )

    assert status == 400
    # 100 应进入业务购买校验，而不是被数量上限拦截。
    assert payload.get("code") == "FORBIDDEN"


def test_shop_buy_rejects_quantity_over_999(monkeypatch):
    monkeypatch.setattr(settlement_extra, "get_user_by_id", lambda _uid: _mock_user())

    payload, status = settlement_extra.settle_shop_buy(
        user_id="u1",
        item_id="hp_pill",
        quantity=1000,
    )

    assert status == 400
    assert payload.get("code") == "INVALID"

