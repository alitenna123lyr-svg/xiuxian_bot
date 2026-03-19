"""Events and world boss services."""

from __future__ import annotations

import random
import time
import math
import json
from typing import Any, Dict, List, Tuple

from core.database.connection import (
    fetch_one,
    db_transaction,
    get_user_by_id,
    refresh_user_stamina,
    spend_user_stamina_tx,
)
from core.utils.number import format_stamina_value
from core.game.events import list_events, get_world_boss_config
from core.services.sect_service import apply_sect_stat_buffs, get_user_sect_buffs
from core.services.metrics_service import log_event, log_economy_ledger
from core.services.worldboss_fsm import WorldBossFSM, WorldBossSnapshot
from core.utils.timeutil import midnight_timestamp, local_day_key

BOSS_DAILY_LIMIT = 5


def _world_boss() -> Dict[str, Any]:
    return get_world_boss_config()


def _ensure_event_point_tables(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS event_points (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            points_total INTEGER DEFAULT 0,
            points_spent INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT 0,
            UNIQUE(user_id, event_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS event_point_logs (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            delta_points INTEGER NOT NULL,
            source TEXT NOT NULL,
            meta_json TEXT,
            created_at INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS event_exchange_claims (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            exchange_id TEXT NOT NULL,
            period_key TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            UNIQUE(user_id, event_id, exchange_id, period_key)
        )
        """
    )


def _event_period_key(now_ts: int, period: str) -> str:
    period = str(period or "event")
    if period == "day":
        return f"day:{local_day_key(now_ts)}"
    if period == "week":
        return f"week:{local_day_key(now_ts) // 7}"
    return "event:all"


def _grant_event_points(cur, user_id: str, event_id: str, points: int, source: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    pts = int(points or 0)
    if pts <= 0:
        cur.execute(
            "SELECT points_total, points_spent FROM event_points WHERE user_id = %s AND event_id = %s",
            (user_id, event_id),
        )
        row = cur.fetchone()
        total = int((row["points_total"] if row else 0) or 0)
        spent = int((row["points_spent"] if row else 0) or 0)
        return {"points_total": total, "points_spent": spent, "points_balance": max(0, total - spent)}
    now = int(time.time())
    _ensure_event_point_tables(cur)
    cur.execute(
        """
        INSERT INTO event_points(user_id, event_id, points_total, points_spent, updated_at)
        VALUES(%s, %s, %s, 0, %s)
        ON CONFLICT(user_id, event_id)
        DO UPDATE SET
            points_total = event_points.points_total + excluded.points_total,
            updated_at = excluded.updated_at
        """,
        (user_id, event_id, pts, now),
    )
    cur.execute(
        "INSERT INTO event_point_logs(user_id, event_id, delta_points, source, meta_json, created_at) VALUES(%s,%s,%s,%s,%s,%s)",
        (user_id, event_id, pts, source, json.dumps(meta or {}, ensure_ascii=False), now),
    )
    cur.execute(
        "SELECT points_total, points_spent FROM event_points WHERE user_id = %s AND event_id = %s",
        (user_id, event_id),
    )
    row = cur.fetchone()
    total = int((row["points_total"] if row else 0) or 0)
    spent = int((row["points_spent"] if row else 0) or 0)
    return {"points_total": total, "points_spent": spent, "points_balance": max(0, total - spent)}


def _apply_action_points(cur, user_id: str, action_key: str, *, now_ts: int, meta: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    action = str(action_key or "").strip()
    if not action:
        return []
    events = []
    for event in get_active_events():
        rules = event.get("point_rules", {}) or {}
        points = int(rules.get(action, 0) or 0)
        if points <= 0:
            continue
        balance = _grant_event_points(cur, user_id, event["id"], points, action, meta=meta)
        events.append({"event_id": event["id"], "granted_points": points, **balance})
    return events


def grant_event_points_for_action(user_id: str, action_key: str, *, meta: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    now = int(time.time())
    with db_transaction() as cur:
        _ensure_event_point_tables(cur)
        return _apply_action_points(cur, user_id, action_key, now_ts=now, meta=meta)


def _grant_generated_item(cur, user_id: str, item_id: str, quantity: int) -> Dict[str, Any] | None:
    from core.game.items import get_item_by_id, generate_material, generate_pill, generate_equipment, Quality

    base = get_item_by_id(item_id)
    if not base:
        return None
    item_type = getattr(base.get("type"), "value", base.get("type"))
    qty = int(quantity or 1)
    if item_type == "pill":
        generated = generate_pill(item_id, qty)
    elif item_type == "material":
        generated = generate_material(item_id, qty)
    else:
        generated = generate_equipment(base, Quality.COMMON, 1)
        generated["quantity"] = qty
    cur.execute(
        """INSERT INTO items (user_id, item_id, item_name, item_type, quality,
           quantity, level, attack_bonus, defense_bonus, hp_bonus, mp_bonus,
           first_round_reduction_pct, crit_heal_pct, element_damage_pct, low_hp_shield_pct)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            user_id,
            generated.get("item_id"),
            generated.get("item_name"),
            generated.get("item_type"),
            generated.get("quality", "common"),
            generated.get("quantity", 1),
            generated.get("level", 1),
            generated.get("attack_bonus", 0),
            generated.get("defense_bonus", 0),
            generated.get("hp_bonus", 0),
            generated.get("mp_bonus", 0),
            generated.get("first_round_reduction_pct", 0),
            generated.get("crit_heal_pct", 0),
            generated.get("element_damage_pct", 0),
            generated.get("low_hp_shield_pct", 0),
        ),
    )
    return generated


def get_active_events() -> List[Dict[str, Any]]:
    now = int(time.time())
    active = []
    for e in list_events():
        if int(e.get("start_ts", 0) or 0) <= now <= int(e.get("end_ts", 0) or 0):
            active.append(e)
    return active


def get_event_status(user_id: str) -> Dict[str, Any]:
    active = get_active_events()
    items = []
    now = int(time.time())
    next_refresh = midnight_timestamp() + 86400
    with db_transaction() as cur:
        _ensure_event_point_tables(cur)
    for e in active:
        row = fetch_one(
            "SELECT last_claim FROM event_claims WHERE user_id = %s AND event_id = %s",
            (user_id, e["id"]),
        )
        last_claim = int(row.get("last_claim", 0) or 0) if row else 0
        claimed_today = last_claim >= midnight_timestamp()
        end_ts = int(e.get("end_ts", 0) or 0)
        remaining_days = 0
        if end_ts > 0:
            remaining_days = max(0, int(math.ceil((end_ts - now) / 86400)))
        points_row = fetch_one(
            "SELECT points_total, points_spent FROM event_points WHERE user_id = %s AND event_id = %s",
            (user_id, e["id"]),
        )
        points_total = int((points_row or {}).get("points_total", 0) or 0)
        points_spent = int((points_row or {}).get("points_spent", 0) or 0)
        points_balance = max(0, points_total - points_spent)
        exchange_status = []
        for exchange in e.get("exchange_shop", []) or []:
            period = exchange.get("period", "event")
            period_key = _event_period_key(now, period)
            claim_row = fetch_one(
                """
                SELECT quantity FROM event_exchange_claims
                WHERE user_id = %s AND event_id = %s AND exchange_id = %s AND period_key = %s
                """,
                (user_id, e["id"], exchange.get("id"), period_key),
            )
            claimed_qty = int((claim_row or {}).get("quantity", 0) or 0)
            limit = int(exchange.get("limit", 0) or 0)
            remaining = max(0, limit - claimed_qty) if limit > 0 else None
            exchange_status.append(
                {
                    **exchange,
                    "claimed": claimed_qty,
                    "remaining": remaining,
                    "period_key": period_key,
                    "can_exchange": points_balance >= int(exchange.get("cost_points", 0) or 0) and (remaining is None or remaining > 0),
                }
            )
        items.append(
            {
                **e,
                "claimed_today": claimed_today,
                "points_total": points_total,
                "points_spent": points_spent,
                "points_balance": points_balance,
                "exchange_status": exchange_status,
            }
        )
        items[-1]["end_ts"] = end_ts
        items[-1]["remaining_days"] = remaining_days
        items[-1]["next_refresh_ts"] = min(next_refresh, end_ts) if end_ts > 0 else next_refresh
    return {"success": True, "events": items}


def claim_event_reward(user_id: str, event_id: str) -> Tuple[Dict[str, Any], int]:
    user = get_user_by_id(user_id)
    if not user:
        log_event("event_claim", user_id=user_id, success=False, reason="USER_NOT_FOUND", meta={"event_id": event_id})
        return {"success": False, "code": "NOT_FOUND", "message": "玩家不存在"}, 404
    active = {e["id"]: e for e in get_active_events()}
    if event_id not in active:
        log_event("event_claim", user_id=user_id, success=False, reason="INVALID", meta={"event_id": event_id})
        return {"success": False, "code": "INVALID", "message": "活动不存在或未开启"}, 400
    e = active[event_id]
    now = int(time.time())

    rewards = e.get("daily_reward", {}) or {}
    points_granted = int((e.get("point_rules", {}) or {}).get("claim_daily", 0) or 0)
    points_info = {"points_total": 0, "points_spent": 0, "points_balance": 0}
    items = rewards.get("items", []) or []
    today_start = midnight_timestamp()
    with db_transaction() as cur:
        _ensure_event_point_tables(cur)
        cur.execute(
            """
            UPDATE event_claims
            SET last_claim = %s, claims = claims + 1
            WHERE user_id = %s AND event_id = %s AND last_claim < %s
            """,
            (now, user_id, event_id, today_start),
        )
        claimed = int(cur.rowcount or 0) > 0
        if not claimed:
            cur.execute(
                "INSERT INTO event_claims (user_id, event_id, last_claim, claims) VALUES (%s, %s, %s, 1)",
                (user_id, event_id, now),
            )
            claimed = int(cur.rowcount or 0) > 0
        if not claimed:
            log_event("event_claim", user_id=user_id, success=False, reason="ALREADY", meta={"event_id": event_id})
            return {"success": False, "code": "ALREADY", "message": "今日已领取"}, 400

        cur.execute(
            "UPDATE users SET copper = copper + %s, exp = exp + %s, gold = gold + %s WHERE user_id = %s",
            (int(rewards.get("copper", 0) or 0), int(rewards.get("exp", 0) or 0), int(rewards.get("gold", 0) or 0), user_id),
        )
        for it in items:
            from core.game.items import get_item_by_id, generate_material, generate_pill, generate_equipment, Quality
            base = get_item_by_id(it.get("item_id"))
            if not base:
                continue
            item_type = getattr(base.get("type"), "value", base.get("type"))
            qty = int(it.get("quantity", 1) or 1)
            if item_type == "pill":
                generated = generate_pill(it.get("item_id"), qty)
            elif item_type == "material":
                generated = generate_material(it.get("item_id"), qty)
            else:
                generated = generate_equipment(base, Quality.COMMON, 1)
                generated["quantity"] = qty
            cur.execute(
                """INSERT INTO items (user_id, item_id, item_name, item_type, quality,
                   quantity, level, attack_bonus, defense_bonus, hp_bonus, mp_bonus,
                   first_round_reduction_pct, crit_heal_pct, element_damage_pct, low_hp_shield_pct)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    user_id,
                    generated.get("item_id"),
                    generated.get("item_name"),
                    generated.get("item_type"),
                    generated.get("quality", "common"),
                    generated.get("quantity", 1),
                    generated.get("level", 1),
                    generated.get("attack_bonus", 0),
                    generated.get("defense_bonus", 0),
                    generated.get("hp_bonus", 0),
                    generated.get("mp_bonus", 0),
                    generated.get("first_round_reduction_pct", 0),
                    generated.get("crit_heal_pct", 0),
                    generated.get("element_damage_pct", 0),
                    generated.get("low_hp_shield_pct", 0),
                ),
            )
        points_info = _grant_event_points(
            cur,
            user_id,
            event_id,
            points_granted,
            "claim_daily",
            meta={"event_id": event_id},
        )

    log_event(
        "event_claim",
        user_id=user_id,
        success=True,
        rank=int(user.get("rank", 1) or 1),
        meta={"event_id": event_id, "items": rewards.get("items", [])},
    )
    log_economy_ledger(
        user_id=user_id,
        module="event",
        action="event_claim",
        delta_copper=int(rewards.get("copper", 0) or 0),
        delta_gold=int(rewards.get("gold", 0) or 0),
        delta_exp=int(rewards.get("exp", 0) or 0),
        success=True,
        rank=int(user.get("rank", 1) or 1),
        meta={"event_id": event_id},
    )
    return {
        "success": True,
        "message": "领取成功",
        "rewards": rewards,
        "points_granted": points_granted,
        "points_balance": int(points_info.get("points_balance", 0) or 0),
        "points_total": int(points_info.get("points_total", 0) or 0),
        "points_spent": int(points_info.get("points_spent", 0) or 0),
    }, 200


def _ensure_boss_state(cur):
    boss = _world_boss()
    cur.execute("SELECT * FROM world_boss_state WHERE boss_id = %s", (boss["id"],))
    row = cur.fetchone()
    if row:
        return row
    cur.execute(
        "INSERT INTO world_boss_state (boss_id, hp, max_hp, last_reset, last_defeated) VALUES (%s, %s, %s, %s, 0)",
        (boss["id"], boss["max_hp"], boss["max_hp"], int(time.time())),
    )
    cur.execute("SELECT * FROM world_boss_state WHERE boss_id = %s", (boss["id"],))
    return cur.fetchone()


def _ensure_worldboss_tables(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS world_boss_state (
            id SERIAL PRIMARY KEY,
            boss_id TEXT UNIQUE NOT NULL,
            hp INTEGER DEFAULT 0,
            max_hp INTEGER DEFAULT 0,
            last_reset INTEGER DEFAULT 0,
            last_defeated INTEGER DEFAULT 0
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS world_boss_attacks (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            last_attack_day INTEGER DEFAULT 0,
            attacks_today INTEGER DEFAULT 0,
            UNIQUE(user_id)
        )
        """
    )


def get_world_boss_status() -> Dict[str, Any]:
    boss_cfg = _world_boss()
    now = int(time.time())
    day_start = midnight_timestamp()
    with db_transaction() as cur:
        _ensure_worldboss_tables(cur)
        row = _ensure_boss_state(cur)
        if row is None:
            return {"success": False, "message": "Boss not found"}
        row_data = dict(row)
        snapshot = WorldBossSnapshot.from_row(row_data, now_ts=now, day_start_ts=day_start)
        fsm = WorldBossFSM(snapshot)
        if fsm.should_daily_reset():
            fsm.apply_daily_reset()
            cur.execute(
                "UPDATE world_boss_state SET hp = %s, last_reset = %s WHERE boss_id = %s",
                (snapshot.hp, snapshot.last_reset, boss_cfg["id"]),
            )
            row = _ensure_boss_state(cur)
            row_data = dict(row) if row is not None else {}
            snapshot = WorldBossSnapshot.from_row(row_data, now_ts=now, day_start_ts=day_start)
            fsm = WorldBossFSM(snapshot)
    return {
        "success": True,
        "boss": {
            "id": boss_cfg["id"],
            "name": boss_cfg["name"],
            "hp": int(row_data.get("hp", 0) or 0),
            "max_hp": int(row_data.get("max_hp", 0) or 0),
            "state": fsm.state.value,
        },
    }


def attack_world_boss(user_id: str) -> Tuple[Dict[str, Any], int]:
    user = get_user_by_id(user_id)
    if not user:
        log_event("world_boss_attack", user_id=user_id, success=False, reason="USER_NOT_FOUND")
        return {"success": False, "code": "NOT_FOUND", "message": "玩家不存在"}, 404
    sect_buffs = get_user_sect_buffs(user_id)
    boss_cfg = _world_boss()

    now = int(time.time())
    stamina_user = refresh_user_stamina(user_id, now=now)
    event_point_grants: List[Dict[str, Any]] = []
    with db_transaction() as cur:
        _ensure_worldboss_tables(cur)
        _ensure_event_point_tables(cur)
        day = local_day_key(now)
        cur.execute(
            "SELECT last_attack_day, attacks_today FROM world_boss_attacks WHERE user_id = %s",
            (user_id,),
        )
        attack_row = cur.fetchone()
        attacks_today = 0
        if attack_row:
            last_day = int(attack_row["last_attack_day"] or 0)
            attacks_today = int(attack_row["attacks_today"] or 0)
            if last_day != day:
                attacks_today = 0
        if attacks_today >= BOSS_DAILY_LIMIT:
            log_event(
                "world_boss_attack",
                user_id=user_id,
                success=False,
                rank=int(user.get("rank", 1) or 1),
                reason="LIMIT",
            )
            return {"success": False, "code": "LIMIT", "message": "今日攻击次数已用完"}, 400

        row = _ensure_boss_state(cur)
        snapshot = WorldBossSnapshot.from_row(row, now_ts=now, day_start_ts=midnight_timestamp())
        fsm = WorldBossFSM(snapshot)
        if fsm.should_daily_reset():
            fsm.apply_daily_reset()
            cur.execute(
                "UPDATE world_boss_state SET hp = %s, last_reset = %s WHERE boss_id = %s",
                (snapshot.hp, snapshot.last_reset, boss_cfg["id"]),
            )
            row = _ensure_boss_state(cur)
            snapshot = WorldBossSnapshot.from_row(row, now_ts=now, day_start_ts=midnight_timestamp())
            fsm = WorldBossFSM(snapshot)

        if not fsm.can_attack():
            log_event(
                "world_boss_attack",
                user_id=user_id,
                success=False,
                rank=int(user.get("rank", 1) or 1),
                reason="DEFEATED",
            )
            return {"success": False, "code": "DEFEATED", "message": "世界BOSS已被击败，请等待刷新"}, 400
        hp = int(snapshot.hp or 0)
        if not spend_user_stamina_tx(cur, user_id, 1, now=now):
            current = get_user_by_id(user_id) or stamina_user or user
            log_event(
                "world_boss_attack",
                user_id=user_id,
                success=False,
                rank=int(user.get("rank", 1) or 1),
                reason="INSUFFICIENT_STAMINA",
            )
            return {
                "success": False,
                "code": "INSUFFICIENT_STAMINA",
                "message": "精力不足，攻击世界BOSS需要 1 点精力",
                "stamina": format_stamina_value((current or {}).get("stamina", 0)),
                "stamina_cost": 1,
            }, 400
        user = get_user_by_id(user_id) or user

        battle_user = apply_sect_stat_buffs(user)
        base = int(battle_user.get("attack", 10) or 10)
        damage = max(1, int(base * random.uniform(0.8, 1.2)))
        new_hp = max(0, hp - damage)

        cur.execute(
            "UPDATE world_boss_state SET hp = %s WHERE boss_id = %s",
            (new_hp, boss_cfg["id"]),
        )

        defeated = new_hp == 0
        rank = int(user.get("rank", 1) or 1)
        rewards = {
            "copper": max(80, min(260, 50 + rank * 8)),
            "exp": max(60, min(220, 40 + rank * 6)),
            "gold": 0,
            "items": [],
        }
        reward_mult = 1.0 + float(sect_buffs.get("battle_reward_pct", 0.0)) / 100.0
        rewards["copper"] = int(round(rewards["copper"] * reward_mult))
        rewards["exp"] = int(round(rewards["exp"] * reward_mult))

        if rank >= 20 and random.random() < 0.18:
            rare_id = "dragon_scale" if random.random() < 0.5 else "phoenix_feather"
            generated = _grant_generated_item(cur, user_id, rare_id, 1)
            if generated:
                rewards["items"].append({"item_id": generated["item_id"], "quantity": generated.get("quantity", 1)})
        elif rank >= 10 and random.random() < 0.28:
            generated = _grant_generated_item(cur, user_id, "demon_core", 1)
            if generated:
                rewards["items"].append({"item_id": generated["item_id"], "quantity": generated.get("quantity", 1)})

        cur.execute(
            "UPDATE users SET copper = copper + %s, exp = exp + %s WHERE user_id = %s",
            (rewards["copper"], rewards["exp"], user_id),
        )

        if defeated:
            rewards["copper"] += boss_cfg["reward_copper"]
            rewards["exp"] += boss_cfg["reward_exp"]
            rewards["gold"] += int(boss_cfg.get("reward_gold", 0) or 0)
            cur.execute(
                "UPDATE users SET copper = copper + %s, exp = exp + %s, gold = gold + %s WHERE user_id = %s",
                (boss_cfg["reward_copper"], boss_cfg["reward_exp"], rewards["gold"], user_id),
            )
            boss_bonus_id = "dragon_scale" if rank >= 20 else "demon_core"
            generated = _grant_generated_item(cur, user_id, boss_bonus_id, 1)
            if generated:
                rewards["items"].append({"item_id": generated["item_id"], "quantity": generated.get("quantity", 1)})
            cur.execute(
                "UPDATE world_boss_state SET last_defeated = %s WHERE boss_id = %s",
                (now, boss_cfg["id"]),
            )

        # update per-user attack count
        if attack_row:
            cur.execute(
                "UPDATE world_boss_attacks SET last_attack_day = %s, attacks_today = %s WHERE user_id = %s",
                (day, attacks_today + 1, user_id),
            )
        else:
            cur.execute(
                "INSERT INTO world_boss_attacks (user_id, last_attack_day, attacks_today) VALUES (%s, %s, %s)",
                (user_id, day, 1),
            )
        event_point_grants = _apply_action_points(
            cur,
            user_id,
            "world_boss_attack",
            now_ts=now,
            meta={"damage": damage, "defeated": defeated},
        )

    log_event(
        "world_boss_attack",
        user_id=user_id,
        success=True,
        rank=int(user.get("rank", 1) or 1),
        meta={"damage": damage, "defeated": defeated},
    )
    log_economy_ledger(
        user_id=user_id,
        module="world_boss",
        action="world_boss_attack",
        delta_copper=int(rewards.get("copper", 0) or 0),
        delta_gold=int(rewards.get("gold", 0) or 0),
        delta_exp=int(rewards.get("exp", 0) or 0),
        delta_stamina=-1,
        success=True,
        rank=int(user.get("rank", 1) or 1),
        meta={"defeated": defeated, "damage": damage},
    )
    return {
        "success": True,
        "damage": damage,
        "boss_hp": new_hp,
        "defeated": defeated,
        "rewards": rewards,
        "attacks_left": max(0, BOSS_DAILY_LIMIT - (attacks_today + 1)),
        "event_points": event_point_grants,
    }, 200


def exchange_event_points(user_id: str, event_id: str, exchange_id: str, *, quantity: int = 1) -> Tuple[Dict[str, Any], int]:
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "code": "NOT_FOUND", "message": "玩家不存在"}, 404
    qty = max(1, int(quantity or 1))
    active_map = {e["id"]: e for e in get_active_events()}
    event = active_map.get(event_id)
    if not event:
        return {"success": False, "code": "INVALID", "message": "活动不存在或未开启"}, 400
    exchange = next((x for x in (event.get("exchange_shop", []) or []) if x.get("id") == exchange_id), None)
    if not exchange:
        return {"success": False, "code": "INVALID", "message": "兑换项不存在"}, 400
    cost_points = max(1, int(exchange.get("cost_points", 0) or 0))
    total_cost = cost_points * qty
    now = int(time.time())
    period = str(exchange.get("period") or "event")
    period_key = _event_period_key(now, period)
    reward_spec = exchange.get("rewards", {}) or {}
    awarded_items: List[Dict[str, Any]] = []

    with db_transaction() as cur:
        _ensure_event_point_tables(cur)
        cur.execute(
            "SELECT points_total, points_spent FROM event_points WHERE user_id = %s AND event_id = %s",
            (user_id, event_id),
        )
        row = cur.fetchone()
        points_total = int((row["points_total"] if row else 0) or 0)
        points_spent = int((row["points_spent"] if row else 0) or 0)
        points_balance = max(0, points_total - points_spent)
        if points_balance < total_cost:
            return {
                "success": False,
                "code": "INSUFFICIENT_POINTS",
                "message": f"积分不足，需要 {total_cost}，当前 {points_balance}",
                "points_balance": points_balance,
            }, 400

        limit = int(exchange.get("limit", 0) or 0)
        cur.execute(
            """
            SELECT quantity FROM event_exchange_claims
            WHERE user_id = %s AND event_id = %s AND exchange_id = %s AND period_key = %s
            """,
            (user_id, event_id, exchange_id, period_key),
        )
        claim_row = cur.fetchone()
        claimed = int((claim_row["quantity"] if claim_row else 0) or 0)
        if limit > 0 and claimed + qty > limit:
            return {
                "success": False,
                "code": "LIMIT",
                "message": f"兑换次数不足，本周期剩余 {max(0, limit - claimed)} 次",
                "remaining": max(0, limit - claimed),
            }, 400

        cur.execute(
            """
            INSERT INTO event_points(user_id, event_id, points_total, points_spent, updated_at)
            VALUES(%s, %s, 0, %s, %s)
            ON CONFLICT(user_id, event_id)
            DO UPDATE SET
                points_spent = event_points.points_spent + excluded.points_spent,
                updated_at = excluded.updated_at
            """,
            (user_id, event_id, total_cost, now),
        )
        cur.execute(
            "INSERT INTO event_point_logs(user_id, event_id, delta_points, source, meta_json, created_at) VALUES(%s,%s,%s,%s,%s,%s)",
            (
                user_id,
                event_id,
                -total_cost,
                "exchange",
                json.dumps({"exchange_id": exchange_id, "quantity": qty}, ensure_ascii=False),
                now,
            ),
        )
        cur.execute(
            """
            INSERT INTO event_exchange_claims(user_id, event_id, exchange_id, period_key, quantity)
            VALUES(%s,%s,%s,%s,%s)
            ON CONFLICT(user_id, event_id, exchange_id, period_key)
            DO UPDATE SET quantity = event_exchange_claims.quantity + excluded.quantity
            """,
            (user_id, event_id, exchange_id, period_key, qty),
        )
        cur.execute(
            "UPDATE users SET copper = copper + %s, exp = exp + %s, gold = gold + %s WHERE user_id = %s",
            (
                int(reward_spec.get("copper", 0) or 0) * qty,
                int(reward_spec.get("exp", 0) or 0) * qty,
                int(reward_spec.get("gold", 0) or 0) * qty,
                user_id,
            ),
        )
        for item in reward_spec.get("items", []) or []:
            generated = _grant_generated_item(
                cur,
                user_id,
                item.get("item_id"),
                int(item.get("quantity", 1) or 1) * qty,
            )
            if generated:
                awarded_items.append({"item_id": generated.get("item_id"), "quantity": int(generated.get("quantity", 1) or 1)})
        cur.execute(
            "SELECT points_total, points_spent FROM event_points WHERE user_id = %s AND event_id = %s",
            (user_id, event_id),
        )
        final_row = cur.fetchone()
        total = int((final_row["points_total"] if final_row else 0) or 0)
        spent = int((final_row["points_spent"] if final_row else 0) or 0)
        balance = max(0, total - spent)

    return {
        "success": True,
        "message": "兑换成功",
        "event_id": event_id,
        "exchange_id": exchange_id,
        "quantity": qty,
        "cost_points": total_cost,
        "points_total": total,
        "points_spent": spent,
        "points_balance": balance,
        "rewards": {
            "copper": int(reward_spec.get("copper", 0) or 0) * qty,
            "exp": int(reward_spec.get("exp", 0) or 0) * qty,
            "gold": int(reward_spec.get("gold", 0) or 0) * qty,
            "items": awarded_items,
        },
    }, 200
