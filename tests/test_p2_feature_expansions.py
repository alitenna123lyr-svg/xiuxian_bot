import time

from core.database.connection import add_item, execute, fetch_one
from core.game.items import generate_material
from core.services import turn_battle_service as tbs
from core.services.alchemy_service import brew_pill
from core.services.drop_pity_service import roll_targeted_drop_with_pity
from core.services.events_service import (
    claim_event_reward,
    exchange_event_points,
    get_active_events,
)
from core.services.forge_service import forge
from core.services.settlement import settle_secret_realm_explore
from core.services.balance_service import hunt_base_exp, hunt_rewards
from tests.conftest import create_user


def test_turn_hunt_session_exposes_kernel_shadow_meta(test_db):
    create_user("u1", "甲", rank=5)
    payload, status = tbs.start_hunt_session("u1", "wild_boar", now=int(time.time()))
    assert status == 200
    assert payload.get("combat_modifiers", {}).get("kernel_shadow", {}).get("enabled") is True


def test_secret_realm_multi_step_returns_node_results(monkeypatch, test_db):
    create_user("u1", "甲", rank=8)
    now = int(time.time())
    nodes = [
        {"type": "monster", "label": "节点1", "monster_id": "wild_boar", "danger_scale": 1.0, "node_path": "normal"},
        {"type": "safe_event", "label": "节点2", "monster_id": None, "danger_scale": 1.0, "node_path": "safe"},
        {"type": "monster", "label": "节点3", "monster_id": "wolf", "danger_scale": 1.0, "node_path": "risky"},
    ]

    monkeypatch.setattr("core.services.settlement.build_secret_realm_node_chain", lambda realm, path="normal", steps=3: list(nodes))
    monkeypatch.setattr(
        "core.services.settlement.hunt_monster",
        lambda *args, **kwargs: {
            "success": True,
            "victory": True,
            "message": "ok",
            "monster": {"name": "M"},
            "attacker_remaining_hp": 88,
            "attacker_remaining_mp": 30,
            "log": ["x"],
            "rounds": 1,
            "rewards": {"gold": 0},
        },
    )
    monkeypatch.setattr(
        "core.services.settlement.roll_secret_realm_rewards",
        lambda *args, **kwargs: {"exp": 10, "copper": 8, "gold": 0, "drop_item_ids": [], "event": "E"},
    )
    monkeypatch.setattr("core.services.settlement.roll_targeted_drop_with_pity", lambda **kwargs: (None, {"next_streak": 1}))

    payload, status = settle_secret_realm_explore(
        user_id="u1",
        realm_id="burning_ruins",
        path="normal",
        request_id=None,
        secret_cooldown_seconds=0,
        now=now,
        multi_step=True,
        multi_step_nodes=3,
    )
    assert status == 200
    assert payload.get("multi_step") is True
    assert payload.get("total_nodes") == 3
    assert payload.get("completed_nodes") == 3
    assert len(payload.get("node_results", [])) == 3


def test_event_points_claim_and_exchange_flow(test_db):
    create_user("u1", "甲", rank=12)
    active = get_active_events()
    assert active
    event = next((e for e in active if e.get("exchange_shop")), active[0])
    event_id = event["id"]
    claim_payload, claim_status = claim_event_reward("u1", event_id)
    assert claim_status == 200
    assert int(claim_payload.get("points_granted", 0)) >= 0

    exchange = (event.get("exchange_shop") or [None])[0]
    if not exchange:
        return
    execute(
        """
        INSERT INTO event_points(user_id, event_id, points_total, points_spent, updated_at)
        VALUES(?, ?, ?, 0, ?)
        ON CONFLICT(user_id, event_id)
        DO UPDATE SET points_total = excluded.points_total, updated_at = excluded.updated_at
        """,
        ("u1", event_id, 999, int(time.time())),
    )
    payload, status = exchange_event_points("u1", event_id, exchange["id"], quantity=1)
    assert status == 200
    assert payload.get("success") is True
    assert int(payload.get("points_balance", 0)) < 999


def test_alchemy_mastery_changes_effective_success_rate(monkeypatch, test_db):
    create_user("u_low", "低", rank=15)
    create_user("u_high", "高", rank=15)
    for uid in ("u_low", "u_high"):
        add_item(uid, generate_material("demon_core", 3))
        add_item(uid, generate_material("recipe_fragment", 3))
        add_item(uid, generate_material("immortal_stone", 3))
    execute("UPDATE users SET alchemy_output_score = %s WHERE user_id = %s", (0, "u_low"))
    execute("UPDATE users SET alchemy_output_score = %s WHERE user_id = %s", (30000, "u_high"))

    monkeypatch.setattr("core.services.alchemy_service.random.random", lambda: 0.55)
    low_payload, low_status = brew_pill("u_low", "recipe_void_break")
    high_payload, high_status = brew_pill("u_high", "recipe_void_break")
    assert low_status == 200
    assert high_status == 200
    assert low_payload.get("brew_success") is False
    assert high_payload.get("brew_success") is True
    assert float(high_payload.get("effective_success_rate", 0)) > float(low_payload.get("effective_success_rate", 0))


def test_forge_high_mode_spends_more_stamina_and_marks_mode(test_db):
    create_user("u1", "甲", rank=12)
    add_item("u1", generate_material("iron_ore", 120))
    cfg = {
        "enabled": True,
        "base_cost_copper": 100,
        "material_item_id": "iron_ore",
        "material_need": 8,
        "reward_pool": [{"item_id": "small_exp_pill", "weight": 1, "qty": 1}],
        "high_invest": {"enabled": True, "cost_mult": 2.0, "material_mult": 2.0, "stamina_cost": 2, "reward_qty_mult": 1.5},
    }
    payload, status = forge(user_id="u1", cfg=cfg, mode="high")
    assert status == 200
    assert payload.get("mode") == "high"
    assert int(payload.get("stamina_cost", 0)) == 2
    row = fetch_one("SELECT stamina FROM users WHERE user_id = %s", ("u1",))
    assert int(row["stamina"]) == 22


def test_drop_pity_accumulates_then_resets(monkeypatch, test_db):
    create_user("u1", "甲", rank=10)
    monkeypatch.setattr("core.game.items.random.random", lambda: 0.99)
    _, m1 = roll_targeted_drop_with_pity(user_id="u1", source_kind="monster", source_id="wolf", user_rank=10, boosted=False)
    _, m2 = roll_targeted_drop_with_pity(user_id="u1", source_kind="monster", source_id="wolf", user_rank=10, boosted=False)
    assert int(m1.get("next_streak", 0)) == 1
    assert int(m2.get("next_streak", 0)) == 2

    monkeypatch.setattr("core.game.items.random.random", lambda: 0.0)
    drop, m3 = roll_targeted_drop_with_pity(user_id="u1", source_kind="monster", source_id="wolf", user_rank=10, boosted=False)
    assert drop is not None
    assert int(m3.get("next_streak", -1)) == 0


def test_piecewise_rank_curve_is_supported():
    plain = hunt_base_exp(15, base=20.0, growth=1.25)
    curved = hunt_base_exp(
        15,
        base=20.0,
        growth=1.25,
        rank_curve=[
            {"max_rank": 10, "growth": 1.25},
            {"max_rank": 20, "growth": 1.10},
        ],
    )
    assert curved < plain


def test_hunt_rewards_scale_with_monster_exp_when_available(monkeypatch):
    monkeypatch.setattr("core.services.balance_service.random.randint", lambda low, high: high)
    cfg = {
        "base_exp": 20,
        "growth": 1.25,
        "copper_ratio": 0.6,
        "copper_rand": 0.2,
        "currency_gain_mult": 0.25,
    }
    rank = 3

    baseline = hunt_rewards(rank, cfg)
    wild = hunt_rewards(rank, cfg, monster={"exp_reward": 20})
    spirit_rat = hunt_rewards(rank, cfg, monster={"exp_reward": 50})
    giant_snake = hunt_rewards(rank, cfg, monster={"exp_reward": 60})

    # Weak monsters should not drop below the rank baseline.
    assert wild["exp"] == baseline["exp"]
    # Stronger monsters should reward more than weaker ones.
    assert spirit_rat["exp"] > wild["exp"]
    assert giant_snake["exp"] > spirit_rat["exp"]
    # Copper uses the same reward base, so higher-exp monsters should trend higher.
    assert spirit_rat["copper"] > wild["copper"]
    assert giant_snake["copper"] > spirit_rat["copper"]
