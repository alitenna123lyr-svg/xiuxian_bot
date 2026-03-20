"""Events and world boss definitions."""

from __future__ import annotations

from typing import Dict, Any, List
from copy import deepcopy

from core.config import config


EVENTS = [
    {
        "id": "spring_festival",
        "name": "春日庆典",
        "desc": "每日领取春日礼盒",
        "start_ts": 1704067200,
        "end_ts": 1893456000,
        "daily_reward": {"copper": 320, "exp": 150, "items": [{"item_id": "herb", "quantity": 3}]},
    },
    {
        "id": "moon_market",
        "name": "月市巡游",
        "desc": "每日领取月市补给",
        "start_ts": 1704067200,
        "end_ts": 1893456000,
        "daily_reward": {"copper": 450, "exp": 200, "gold": 1, "items": [{"item_id": "spirit_stone", "quantity": 2}]},
    },
    {
        "id": "trial_arena",
        "name": "试炼擂台",
        "desc": "每日领取试炼奖励",
        "start_ts": 1704067200,
        "end_ts": 1893456000,
        "daily_reward": {"copper": 300, "exp": 220, "gold": 1, "items": [{"item_id": "breakthrough_pill", "quantity": 1}]},
    },
]


WORLD_BOSS = {
    "id": "world_boss_1",
    "name": "赤炎妖王",
    "max_hp": 100000,
    "reward_copper": 1200,
    "reward_exp": 1200,
    "reward_gold": 2,
}


def _normalize_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    event = deepcopy(raw or {})
    event["id"] = str(event.get("id") or "").strip()
    event["name"] = str(event.get("name") or event["id"] or "活动")
    event["desc"] = str(event.get("desc") or "")
    event["start_ts"] = int(event.get("start_ts", 0) or 0)
    event["end_ts"] = int(event.get("end_ts", 0) or 0)
    reward = event.get("daily_reward", {}) or {}
    event["daily_reward"] = {
        "copper": int(reward.get("copper", 0) or 0),
        "exp": int(reward.get("exp", 0) or 0),
        "gold": int(reward.get("gold", 0) or 0),
        "items": reward.get("items", []) or [],
    }
    point_rules = event.get("point_rules", {}) or {}
    event["point_rules"] = {
        "claim_daily": int(point_rules.get("claim_daily", 0) or 0),
        "world_boss_attack": int(point_rules.get("world_boss_attack", 0) or 0),
        "hunt_victory": int(point_rules.get("hunt_victory", 0) or 0),
        "secret_victory": int(point_rules.get("secret_victory", 0) or 0),
    }
    exchange_shop = []
    for row in event.get("exchange_shop", []) or []:
        if not isinstance(row, dict):
            continue
        exchange_id = str(row.get("id") or "").strip()
        if not exchange_id:
            continue
        exchange_shop.append(
            {
                "id": exchange_id,
                "name": str(row.get("name") or exchange_id),
                "cost_points": max(1, int(row.get("cost_points", 0) or 0)),
                "limit": max(0, int(row.get("limit", 0) or 0)),
                "period": str(row.get("period") or "event"),
                "rewards": row.get("rewards", {}) or {},
            }
        )
    event["exchange_shop"] = exchange_shop
    return event


def list_events() -> List[Dict[str, Any]]:
    configured = config.get_nested("events", "catalog", default=None)
    source = configured if isinstance(configured, list) and configured else EVENTS
    events: List[Dict[str, Any]] = []
    for raw in source:
        normalized = _normalize_event(raw if isinstance(raw, dict) else {})
        if normalized.get("id"):
            events.append(normalized)
    return events


def get_world_boss_config() -> Dict[str, Any]:
    def _to_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)

    configured = config.get_nested("events", "world_boss", default=None)
    if not isinstance(configured, dict):
        return deepcopy(WORLD_BOSS)
    merged = deepcopy(WORLD_BOSS)
    merged.update(configured)
    merged["id"] = str(merged.get("id") or WORLD_BOSS["id"])
    merged["name"] = str(merged.get("name") or WORLD_BOSS["name"])
    merged["max_hp"] = max(1, _to_int(merged.get("max_hp", WORLD_BOSS["max_hp"]), WORLD_BOSS["max_hp"]))
    merged["reward_copper"] = max(0, _to_int(merged.get("reward_copper", WORLD_BOSS["reward_copper"]), WORLD_BOSS["reward_copper"]))
    merged["reward_exp"] = max(0, _to_int(merged.get("reward_exp", WORLD_BOSS["reward_exp"]), WORLD_BOSS["reward_exp"]))
    merged["reward_gold"] = max(0, _to_int(merged.get("reward_gold", WORLD_BOSS.get("reward_gold", 0)), WORLD_BOSS.get("reward_gold", 0)))
    return merged
