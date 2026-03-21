import importlib.util

import pytest

_HAS_PSYCOPG2 = importlib.util.find_spec("psycopg2") is not None

if _HAS_PSYCOPG2:
    from core.services import settlement_extra
else:  # pragma: no cover - dependency-gated in CI/local envs without psycopg2
    settlement_extra = None

pytestmark = pytest.mark.skipif(not _HAS_PSYCOPG2, reason="requires psycopg2")


def test_protect_strategy_uses_copper_budget(monkeypatch):
    user = {
        "user_id": "u1",
        "rank": 1,
        "exp": 999999,
        "copper": 101,
        "stamina": 10,
        "element": "金",
        "breakthrough_pity": 0,
        "breakthrough_protect_until": 0,
        "breakthrough_boost_until": 0,
        "breakthrough_boost_pct": 0,
    }

    monkeypatch.setattr(settlement_extra, "get_user_by_id", lambda _uid: user)
    monkeypatch.setattr(settlement_extra, "is_realm_trial_complete", lambda _uid, _rank: True)
    monkeypatch.setattr(
        settlement_extra,
        "_breakthrough_cfg",
        lambda: {
            "fire_bonus": 0.03,
            "steady_bonus": 0.10,
            "post_breakthrough_restore_ratio": 0.30,
            "stamina_cost": 1,
            "protect_material_base": 2,
            "protect_material_per_10_rank": 0,
            "desperate_exp_penalty_add": 0.05,
            "desperate_exp_penalty_cap": 0.30,
            "desperate_weak_seconds_add": 1800,
            "desperate_success_gold_bonus": 1,
            "desperate_success_copper_min": 50,
            "desperate_success_copper_cost_divisor": 5,
        },
    )

    monkeypatch.setattr("core.game.realms.can_breakthrough", lambda _exp, _rank: True)
    monkeypatch.setattr("core.game.realms.calculate_breakthrough_cost", lambda _rank: 100)

    resp, status = settlement_extra.settle_breakthrough(user_id="u1", use_pill=False, strategy="protect")

    assert status == 400
    assert resp.get("code") == "INSUFFICIENT_COPPER"
    assert "102" in str(resp.get("message", ""))


def test_protect_preview_reports_total_copper_cost(monkeypatch):
    user = {
        "user_id": "u1",
        "rank": 1,
        "exp": 999999,
        "copper": 999999,
        "stamina": 10,
        "element": "金",
        "breakthrough_pity": 0,
        "breakthrough_protect_until": 0,
        "breakthrough_boost_until": 0,
        "breakthrough_boost_pct": 0,
    }

    monkeypatch.setattr(settlement_extra, "get_user_by_id", lambda _uid: user)
    monkeypatch.setattr(
        settlement_extra,
        "_breakthrough_cfg",
        lambda: {
            "fire_bonus": 0.03,
            "steady_bonus": 0.10,
            "post_breakthrough_restore_ratio": 0.30,
            "stamina_cost": 1,
            "protect_material_base": 2,
            "protect_material_per_10_rank": 0,
            "desperate_exp_penalty_add": 0.05,
            "desperate_exp_penalty_cap": 0.30,
            "desperate_weak_seconds_add": 1800,
            "desperate_success_gold_bonus": 1,
            "desperate_success_copper_min": 50,
            "desperate_success_copper_cost_divisor": 5,
        },
    )
    monkeypatch.setattr("core.game.realms.get_realm_by_id", lambda _rank: {"name": "炼气"})
    monkeypatch.setattr("core.game.realms.get_next_realm", lambda _rank: {"id": 2, "name": "筑基", "break_rate": 0.5})
    monkeypatch.setattr("core.game.realms.calculate_breakthrough_cost", lambda _rank: 100)

    resp, status = settlement_extra.get_breakthrough_preview(user_id="u1", strategy="protect")

    assert status == 200
    assert resp.get("success") is True
    preview = (resp.get("preview") or {})
    assert int(preview.get("base_cost_copper", 0)) == 100
    assert int(preview.get("extra_cost_copper", 0)) == 2
    assert int(preview.get("cost_copper", 0)) == 102
