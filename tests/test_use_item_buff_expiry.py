import time

from core.services import settlement_extra


class _DummyTx:
    def __init__(self):
        self.calls = []
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        self.rowcount = 1


def _patch_use_item_deps(monkeypatch, *, user, base_item):
    monkeypatch.setattr(settlement_extra, "refresh_user_vitals", lambda _uid: None)
    monkeypatch.setattr(settlement_extra, "get_user_by_id", lambda _uid: dict(user))
    monkeypatch.setattr(
        settlement_extra,
        "get_item_by_id",
        lambda _item_id: dict(base_item) if str(_item_id) == str(base_item.get("id")) else None,
    )
    monkeypatch.setattr(
        settlement_extra,
        "_consume_one_item_tx",
        lambda _cur, *, user_id, item_id: True,
    )
    holder = {"tx": None}

    def _open_tx():
        tx = _DummyTx()
        holder["tx"] = tx
        return tx

    monkeypatch.setattr(settlement_extra, "db_transaction", _open_tx)
    return holder


def test_breakthrough_buff_expired_high_value_is_not_carried_forward(monkeypatch):
    now = int(time.time())
    user = {
        "user_id": "u1",
        "breakthrough_boost_until": now - 120,
        "breakthrough_boost_pct": 50,
    }
    base_item = {
        "id": "advanced_breakthrough_pill",
        "effect": "breakthrough",
        "value": 20,
        "duration": 3600,
    }
    holder = _patch_use_item_deps(monkeypatch, user=user, base_item=base_item)

    payload, status = settlement_extra.settle_use_item(user_id="u1", item_id="advanced_breakthrough_pill")

    assert status == 200
    assert payload.get("success") is True
    assert int(payload.get("value", 0) or 0) == 20
    _, params = holder["tx"].calls[-1]
    assert int(params[1] or 0) == 20


def test_breakthrough_buff_keeps_active_higher_value(monkeypatch):
    now = int(time.time())
    user = {
        "user_id": "u1",
        "breakthrough_boost_until": now + 600,
        "breakthrough_boost_pct": 50,
    }
    base_item = {
        "id": "advanced_breakthrough_pill",
        "effect": "breakthrough",
        "value": 20,
        "duration": 3600,
    }
    holder = _patch_use_item_deps(monkeypatch, user=user, base_item=base_item)

    payload, status = settlement_extra.settle_use_item(user_id="u1", item_id="advanced_breakthrough_pill")

    assert status == 200
    assert payload.get("success") is True
    assert int(payload.get("value", 0) or 0) == 50
    _, params = holder["tx"].calls[-1]
    assert int(params[1] or 0) == 50


def test_spirit_array_expired_high_value_is_not_carried_forward(monkeypatch):
    now = int(time.time())
    user = {
        "user_id": "u1",
        "breakthrough_boost_until": now - 60,
        "breakthrough_boost_pct": 50,
        "max_mp": 200,
        "mp": 10,
    }
    base_item = {
        "id": "spirit_array_high",
        "effect": "spirit_array",
        "value": 25,
        "value_pct": 0.50,
        "duration": 10800,
    }
    holder = _patch_use_item_deps(monkeypatch, user=user, base_item=base_item)

    payload, status = settlement_extra.settle_use_item(user_id="u1", item_id="spirit_array_high")

    assert status == 200
    assert payload.get("success") is True
    assert int(payload.get("value", 0) or 0) == 25
    _, params = holder["tx"].calls[-1]
    assert int(params[1] or 0) == 25
