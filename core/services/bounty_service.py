"""Global bounty board service."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from core.database.connection import db_transaction, fetch_all, fetch_one, get_user_by_id
from core.game.items import get_item_by_id
from core.services.audit_log_service import write_audit_log
from core.services.metrics_service import log_event, log_economy_ledger


BOUNTY_STATUS_OPEN = "open"
BOUNTY_STATUS_CLAIMED = "claimed"
BOUNTY_STATUS_COMPLETED = "completed"
BOUNTY_STATUS_CANCELLED = "cancelled"


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _deduct_item_tx(cur: Any, *, user_id: str, item_id: str, quantity: int) -> Dict[str, Any] | None:
    need = max(1, int(quantity or 1))
    cur.execute(
        """
        SELECT id, user_id, item_id, item_name, item_type, quality, quantity, level,
               attack_bonus, defense_bonus, hp_bonus, mp_bonus,
               first_round_reduction_pct, crit_heal_pct, element_damage_pct, low_hp_shield_pct
        FROM items
        WHERE user_id = %s AND item_id = %s
        ORDER BY id ASC
        """,
        (user_id, item_id),
    )
    rows = cur.fetchall() or []
    total = sum(_as_int(row.get("quantity", 0), 0) for row in rows)
    if total < need:
        return None
    template = dict(rows[0])
    remain = need
    for row in rows:
        if remain <= 0:
            break
        row_qty = _as_int(row.get("quantity", 0), 0)
        consume = min(remain, row_qty)
        if consume <= 0:
            continue
        if consume == row_qty:
            cur.execute("DELETE FROM items WHERE id = %s", (row["id"],))
        else:
            cur.execute("UPDATE items SET quantity = quantity - %s WHERE id = %s", (consume, row["id"]))
        remain -= consume
    return template


def _grant_item_tx(cur: Any, *, user_id: str, template: Dict[str, Any], quantity: int) -> None:
    qty = max(1, int(quantity or 1))
    item_id = str(template.get("item_id") or "")
    item_type = str(template.get("item_type") or "material")
    quality = str(template.get("quality") or "common")
    level = max(1, _as_int(template.get("level", 1), 1))
    cur.execute(
        """
        SELECT id FROM items
        WHERE user_id = %s AND item_id = %s AND item_type = %s AND quality = %s AND level = %s
        ORDER BY id ASC LIMIT 1
        """,
        (user_id, item_id, item_type, quality, level),
    )
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE items SET quantity = quantity + %s WHERE id = %s", (qty, row["id"]))
        return
    cur.execute(
        """
        INSERT INTO items (
            user_id, item_id, item_name, item_type, quality, quantity, level,
            attack_bonus, defense_bonus, hp_bonus, mp_bonus,
            first_round_reduction_pct, crit_heal_pct, element_damage_pct, low_hp_shield_pct
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            item_id,
            template.get("item_name") or item_id,
            item_type,
            quality,
            qty,
            level,
            _as_int(template.get("attack_bonus", 0), 0),
            _as_int(template.get("defense_bonus", 0), 0),
            _as_int(template.get("hp_bonus", 0), 0),
            _as_int(template.get("mp_bonus", 0), 0),
            float(template.get("first_round_reduction_pct", 0) or 0),
            float(template.get("crit_heal_pct", 0) or 0),
            float(template.get("element_damage_pct", 0) or 0),
            float(template.get("low_hp_shield_pct", 0) or 0),
        ),
    )


def publish_bounty(
    *,
    user_id: str,
    wanted_item_id: str,
    wanted_quantity: int,
    reward_spirit_low: int,
    description: str = "",
) -> Tuple[Dict[str, Any], int]:
    poster = get_user_by_id(user_id)
    if not poster:
        return {"success": False, "code": "USER_NOT_FOUND", "message": "玩家不存在"}, 404

    item_id = str(wanted_item_id or "").strip()
    if not item_id:
        return {"success": False, "code": "MISSING_PARAMS", "message": "缺少道具ID"}, 400
    item_def = get_item_by_id(item_id)
    if not item_def:
        return {"success": False, "code": "INVALID_ITEM", "message": "道具不存在，无法发布悬赏"}, 400

    qty = _as_int(wanted_quantity, 0)
    reward = _as_int(reward_spirit_low, 0)
    if qty <= 0:
        return {"success": False, "code": "INVALID_QTY", "message": "悬赏数量必须大于 0"}, 400
    if reward <= 0:
        return {"success": False, "code": "INVALID_REWARD", "message": "悬赏奖励必须大于 0"}, 400

    now = int(time.time())
    desc = str(description or "").strip()
    with db_transaction() as cur:
        cur.execute(
            """
            INSERT INTO bounty_orders (
                poster_user_id, wanted_item_id, wanted_item_name, wanted_quantity,
                reward_spirit_low, description, status, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, item_id, item_def.get("name") or item_id, qty, reward, desc, BOUNTY_STATUS_OPEN, now),
        )
        row = cur.fetchone()
        bounty_id = int(row["id"])

    log_event(
        "bounty_publish",
        user_id=user_id,
        success=True,
        rank=int(poster.get("rank", 1) or 1),
        meta={"bounty_id": bounty_id, "item_id": item_id, "qty": qty, "reward_low": reward},
    )
    write_audit_log(
        module="bounty",
        action="publish",
        user_id=user_id,
        success=True,
        detail={"bounty_id": bounty_id, "item_id": item_id, "qty": qty, "reward_spirit_low": reward},
    )
    return {
        "success": True,
        "bounty_id": bounty_id,
        "message": f"悬赏已发布：需要 {qty} 个 {item_def.get('name', item_id)}，奖励 {reward} 下品灵石",
    }, 200


def list_bounties(*, status: str = BOUNTY_STATUS_OPEN, limit: int = 30) -> Tuple[Dict[str, Any], int]:
    st = str(status or BOUNTY_STATUS_OPEN).strip().lower()
    if st not in {BOUNTY_STATUS_OPEN, BOUNTY_STATUS_CLAIMED, BOUNTY_STATUS_COMPLETED, BOUNTY_STATUS_CANCELLED, "all"}:
        return {"success": False, "code": "INVALID_STATUS", "message": "状态参数无效"}, 400
    lim = max(1, min(100, _as_int(limit, 30)))
    if st == "all":
        rows = fetch_all(
            """
            SELECT b.*, p.in_game_username AS poster_name, c.in_game_username AS claimer_name
            FROM bounty_orders b
            LEFT JOIN users p ON p.user_id = b.poster_user_id
            LEFT JOIN users c ON c.user_id = b.claimer_user_id
            ORDER BY b.created_at DESC
            LIMIT %s
            """,
            (lim,),
        )
    else:
        rows = fetch_all(
            """
            SELECT b.*, p.in_game_username AS poster_name, c.in_game_username AS claimer_name
            FROM bounty_orders b
            LEFT JOIN users p ON p.user_id = b.poster_user_id
            LEFT JOIN users c ON c.user_id = b.claimer_user_id
            WHERE b.status = %s
            ORDER BY b.created_at DESC
            LIMIT %s
            """,
            (st, lim),
        )
    return {"success": True, "bounties": [dict(row) for row in rows]}, 200


def accept_bounty(*, user_id: str, bounty_id: int) -> Tuple[Dict[str, Any], int]:
    claimer = get_user_by_id(user_id)
    if not claimer:
        return {"success": False, "code": "USER_NOT_FOUND", "message": "玩家不存在"}, 404

    row = fetch_one("SELECT * FROM bounty_orders WHERE id = %s", (int(bounty_id),))
    if not row:
        return {"success": False, "code": "NOT_FOUND", "message": "悬赏不存在"}, 404
    if str(row.get("poster_user_id")) == str(user_id):
        return {"success": False, "code": "INVALID", "message": "不能接受自己发布的悬赏"}, 400
    if str(row.get("status")) != BOUNTY_STATUS_OPEN:
        return {"success": False, "code": "INVALID_STATUS", "message": "悬赏当前不可接取"}, 400

    now = int(time.time())
    with db_transaction() as cur:
        cur.execute(
            """
            UPDATE bounty_orders
            SET status = %s, claimer_user_id = %s, claimed_at = %s
            WHERE id = %s AND status = %s
            """,
            (BOUNTY_STATUS_CLAIMED, user_id, now, int(bounty_id), BOUNTY_STATUS_OPEN),
        )
        if cur.rowcount == 0:
            return {"success": False, "code": "INVALID_STATUS", "message": "悬赏已被他人接取"}, 400

    write_audit_log(
        module="bounty",
        action="accept",
        user_id=user_id,
        target_user_id=str(row.get("poster_user_id") or ""),
        success=True,
        detail={"bounty_id": int(bounty_id)},
    )
    return {"success": True, "message": "已接受悬赏", "bounty_id": int(bounty_id)}, 200


def submit_bounty(*, user_id: str, bounty_id: int) -> Tuple[Dict[str, Any], int]:
    claimer = get_user_by_id(user_id)
    if not claimer:
        return {"success": False, "code": "USER_NOT_FOUND", "message": "玩家不存在"}, 404
    now = int(time.time())

    with db_transaction() as cur:
        cur.execute("SELECT * FROM bounty_orders WHERE id = %s", (int(bounty_id),))
        bounty = cur.fetchone()
        if not bounty:
            return {"success": False, "code": "NOT_FOUND", "message": "悬赏不存在"}, 404
        bounty = dict(bounty)
        if str(bounty.get("status")) != BOUNTY_STATUS_CLAIMED:
            return {"success": False, "code": "INVALID_STATUS", "message": "该悬赏未处于进行中"}, 400
        if str(bounty.get("claimer_user_id") or "") != str(user_id):
            return {"success": False, "code": "FORBIDDEN", "message": "仅接取者可提交悬赏"}, 403

        poster_id = str(bounty.get("poster_user_id") or "")
        poster = get_user_by_id(poster_id)
        if not poster:
            return {"success": False, "code": "POSTER_NOT_FOUND", "message": "发布者不存在"}, 404

        wanted_item_id = str(bounty.get("wanted_item_id") or "")
        wanted_qty = _as_int(bounty.get("wanted_quantity", 0), 0)
        reward_low = _as_int(bounty.get("reward_spirit_low", 0), 0)
        if int(poster.get("copper", 0) or 0) < reward_low:
            return {"success": False, "code": "POSTER_FUNDS", "message": "发布者下品灵石不足，暂无法结算"}, 400

        template = _deduct_item_tx(cur, user_id=user_id, item_id=wanted_item_id, quantity=wanted_qty)
        if not template:
            return {"success": False, "code": "INSUFFICIENT_ITEM", "message": "提交失败，你的道具数量不足"}, 400

        _grant_item_tx(cur, user_id=poster_id, template=template, quantity=wanted_qty)

        cur.execute(
            "UPDATE users SET copper = copper - %s WHERE user_id = %s AND copper >= %s",
            (reward_low, poster_id, reward_low),
        )
        if cur.rowcount == 0:
            return {"success": False, "code": "POSTER_FUNDS", "message": "发布者下品灵石不足，暂无法结算"}, 400
        cur.execute("UPDATE users SET copper = copper + %s WHERE user_id = %s", (reward_low, user_id))

        cur.execute(
            "UPDATE bounty_orders SET status = %s, completed_at = %s WHERE id = %s",
            (BOUNTY_STATUS_COMPLETED, now, int(bounty_id)),
        )

    log_event(
        "bounty_submit",
        user_id=user_id,
        success=True,
        rank=int(claimer.get("rank", 1) or 1),
        meta={"bounty_id": int(bounty_id), "item_id": wanted_item_id, "qty": wanted_qty, "reward_low": reward_low},
    )
    log_economy_ledger(
        user_id=user_id,
        module="bounty",
        action="bounty_submit",
        delta_copper=reward_low,
        success=True,
        rank=int(claimer.get("rank", 1) or 1),
        meta={"bounty_id": int(bounty_id), "poster_user_id": poster_id},
    )
    write_audit_log(
        module="bounty",
        action="submit",
        user_id=user_id,
        target_user_id=poster_id,
        success=True,
        detail={"bounty_id": int(bounty_id), "item_id": wanted_item_id, "qty": wanted_qty, "reward_spirit_low": reward_low},
    )
    return {
        "success": True,
        "message": f"悬赏已完成，获得 {reward_low} 下品灵石",
        "bounty_id": int(bounty_id),
        "reward_spirit_low": reward_low,
    }, 200
