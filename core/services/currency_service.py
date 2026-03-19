"""Unified currency service."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from core.database.connection import db_transaction, get_user_by_id
from core.game.currency import (
    CURRENCY_DEFINITIONS,
    DACHENG_MIN_RANK,
    EXCHANGE_RATE,
    ZHENXIAN_MIN_RANK,
    calc_exchange_amounts,
    can_gain_currency,
    can_hold_currency,
    currency_label,
    get_currency_definition,
    is_adjacent_exchange,
    next_tier_currency,
    normalize_currency_id,
    prev_tier_currency,
    to_db_field,
    wallet_from_user,
)
from core.services.audit_log_service import write_audit_log


def _is_immortal_currency(currency_id: str) -> bool:
    row = get_currency_definition(currency_id) or {}
    return str(row.get("group")) == "immortal"


def _is_known_currency(rank: int, currency_id: str) -> bool:
    if not _is_immortal_currency(currency_id):
        return True
    return int(rank or 0) >= int(DACHENG_MIN_RANK)


def _is_unlocked_currency(rank: int, currency_id: str) -> bool:
    if not _is_immortal_currency(currency_id):
        return True
    return int(rank or 0) >= int(ZHENXIAN_MIN_RANK)


def get_currency_overview(user_id: str) -> Tuple[Dict[str, Any], int]:
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "code": "NOT_FOUND", "message": "玩家不存在"}, 404
    rank = int(user.get("rank", 1) or 1)
    wallet = wallet_from_user(user)
    tiers = []
    for row in CURRENCY_DEFINITIONS:
        cid = str(row["id"])
        if not _is_known_currency(rank, cid):
            continue
        unlocked = _is_unlocked_currency(rank, cid)
        amount_visible = unlocked or not _is_immortal_currency(cid)
        tiers.append(
            {
                "id": cid,
                "label": row.get("label"),
                "group": row.get("group"),
                "tier": int(row.get("tier", 1) or 1),
                "amount": int(wallet.get(cid, 0) or 0) if amount_visible else 0,
                "known": True,
                "unlocked": bool(unlocked),
                "hold_min_rank": int(row.get("hold_min_rank", 1) or 1),
                "gain_min_rank": int(row.get("gain_min_rank", 1) or 1),
                "can_hold": can_hold_currency(rank, cid),
                "can_gain": can_gain_currency(rank, cid),
                "locked_reason": ("" if unlocked else "仙石需飞升仙界后开启"),
            }
        )
    return {
        "success": True,
        "rank": rank,
        "wallet": wallet,
        "tiers": tiers,
        "rules": {
            "exchange_rate": EXCHANGE_RATE,
            "adjacent_exchange_only": True,
            "immortal_known_min_rank": DACHENG_MIN_RANK,
            "immortal_unlock_min_rank": ZHENXIAN_MIN_RANK,
            "note": "仙石体系：大乘以上才知晓，个人飞升仙界后开启。",
        },
    }, 200


def exchange_currency(
    *,
    user_id: str,
    from_currency: str,
    amount: int,
    to_currency: str | None = None,
) -> Tuple[Dict[str, Any], int]:
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "code": "NOT_FOUND", "message": "玩家不存在"}, 404

    try:
        amount_int = int(amount)
    except (TypeError, ValueError):
        return {"success": False, "code": "INVALID_AMOUNT", "message": "兑换数量必须是整数"}, 400
    if amount_int <= 0:
        return {"success": False, "code": "INVALID_AMOUNT", "message": "兑换数量必须大于 0"}, 400

    src = normalize_currency_id(from_currency)
    dst = normalize_currency_id(to_currency) if to_currency is not None else None
    if not src:
        return {"success": False, "code": "INVALID_CURRENCY", "message": "源货币无效"}, 400

    if dst is None:
        # backward compatibility
        if src == "spirit_low":
            dst = next_tier_currency(src)
        elif src == "spirit_mid":
            dst = prev_tier_currency(src)
        else:
            return {"success": False, "code": "MISSING_TO", "message": "该兑换路径请指定目标货币"}, 400
    if not dst:
        return {"success": False, "code": "INVALID_CURRENCY", "message": "目标货币无效"}, 400

    if not is_adjacent_exchange(src, dst):
        return {"success": False, "code": "INVALID_PATH", "message": "仅支持同体系相邻档位兑换"}, 400

    rank = int(user.get("rank", 1) or 1)
    if not _is_known_currency(rank, src) or not _is_known_currency(rank, dst):
        return {"success": False, "code": "UNKNOWN", "message": "当前境界尚未知晓该货币"}, 400
    if not _is_unlocked_currency(rank, src) or not _is_unlocked_currency(rank, dst):
        return {"success": False, "code": "LOCKED", "message": "仙石体系需飞升仙界后开启"}, 400
    if not can_hold_currency(rank, src) or not can_hold_currency(rank, dst):
        return {"success": False, "code": "RANK_LIMIT", "message": "当前境界不可持有该货币"}, 400
    if not can_gain_currency(rank, dst):
        return {"success": False, "code": "RANK_LIMIT", "message": "当前境界不可获得目标货币"}, 400

    spend_src, gain_dst = calc_exchange_amounts(src, dst, amount_int)
    if spend_src <= 0 or gain_dst <= 0:
        return {
            "success": False,
            "code": "TOO_SMALL",
            "message": f"兑换数量不足，当前比例为 1:{EXCHANGE_RATE}",
        }, 400

    src_field = to_db_field(src)
    dst_field = to_db_field(dst)
    if not src_field or not dst_field:
        return {"success": False, "code": "UNAVAILABLE", "message": "兑换字段配置缺失"}, 400

    if int(user.get(src_field, 0) or 0) < spend_src:
        return {"success": False, "code": "INSUFFICIENT", "message": f"{currency_label(src)}不足"}, 400

    with db_transaction() as cur:
        cur.execute(
            f"UPDATE users SET {src_field} = {src_field} - %s, {dst_field} = {dst_field} + %s "
            f"WHERE user_id = %s AND {src_field} >= %s",
            (spend_src, gain_dst, user_id, spend_src),
        )
        if cur.rowcount == 0:
            return {"success": False, "code": "INSUFFICIENT", "message": f"{currency_label(src)}不足"}, 400

    latest = get_user_by_id(user_id) or user
    wallet = wallet_from_user(latest)
    write_audit_log(
        module="currency",
        action="exchange",
        user_id=user_id,
        success=True,
        detail={
            "from_currency": src,
            "to_currency": dst,
            "input_amount": amount_int,
            "spent": spend_src,
            "gained": gain_dst,
        },
    )
    return {
        "success": True,
        "message": f"兑换成功：{spend_src} {currency_label(src)} -> {gain_dst} {currency_label(dst)}",
        "from_currency": src,
        "to_currency": dst,
        "input_amount": amount_int,
        "spent": spend_src,
        "gained": gain_dst,
        "wallet": wallet,
    }, 200
