"""商店 / 物品使用路由。"""

from flask import Blueprint, request, jsonify

from core.routes._helpers import error, success, log_action, parse_json_payload, resolve_actor_user_id
from core.game.items import get_shop_items, get_item_by_id
from core.services.settlement_extra import settle_shop_buy, settle_use_item, get_shop_remaining_limit
from core.database.connection import get_user_by_id

shop_bp = Blueprint("shop", __name__)


@shop_bp.route("/api/shop", methods=["GET"])
def shop_list():
    """获取商店物品"""
    currency = request.args.get("currency", "copper")
    user_id = request.args.get("user_id")
    if user_id:
        _, auth_error = resolve_actor_user_id({"user_id": user_id})
        if auth_error:
            return auth_error
    items = get_shop_items(currency)
    if user_id and get_user_by_id(user_id):
        enriched = []
        for item in items:
            row = item.copy()
            item_id = str(row.get("item_id", "") or "")
            if not row.get("name"):
                base = get_item_by_id(item_id) or {}
                row["name"] = str(base.get("name") or item_id or "未知物品")
            row["remaining_limit"] = get_shop_remaining_limit(user_id, item["item_id"], item)
            enriched.append(row)
        items = enriched
    else:
        hydrated = []
        for item in items:
            row = item.copy()
            item_id = str(row.get("item_id", "") or "")
            if not row.get("name"):
                base = get_item_by_id(item_id) or {}
                row["name"] = str(base.get("name") or item_id or "未知物品")
            hydrated.append(row)
        items = hydrated
    return success(items=items, currency=currency)


@shop_bp.route("/api/shop/buy", methods=["POST"])
def shop_buy():
    """购买物品"""
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)
    currency = data.get("currency")
    request_id = data.get("request_id")
    log_action("shop_buy", user_id=user_id, request_id=request_id, item_id=item_id, quantity=quantity)

    if not item_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)

    try:
        quantity = int(quantity or 1)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid quantity", 400)

    if quantity <= 0:
        return error("INVALID", "Quantity must be greater than 0", 400)

    if currency is not None:
        currency = str(currency).strip().lower()
        if currency not in ("copper", "gold", "spirit_high"):
            return error("INVALID", "Invalid currency", 400)

    resp, http_status = settle_shop_buy(
        user_id=user_id,
        item_id=item_id,
        quantity=quantity,
        currency=currency,
        request_id=request_id,
    )
    return jsonify(resp), http_status


@shop_bp.route("/api/item/use", methods=["POST"])
def use_item():
    """使用物品"""
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    item_id = data.get("item_id")
    log_action("use_item", user_id=user_id, item_id=item_id)

    if not item_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)

    resp, http_status = settle_use_item(user_id=user_id, item_id=item_id)
    return jsonify(resp), http_status
