"""Unified currency routes."""

from flask import Blueprint, jsonify

from core.routes._helpers import (
    error,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.services.currency_service import get_currency_overview, exchange_currency


currency_bp = Blueprint("currency", __name__)


@currency_bp.route("/api/currency/<user_id>", methods=["GET"])
def currency_overview(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    resp, status = get_currency_overview(user_id)
    return jsonify(resp), status


@currency_bp.route("/api/currency/exchange", methods=["POST"])
def currency_exchange():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    from_currency = data.get("from_currency")
    to_currency = data.get("to_currency")
    amount = data.get("amount")
    if not from_currency or amount is None:
        return error("MISSING_PARAMS", "Missing from_currency or amount", 400)
    log_action("currency_exchange", user_id=user_id, from_currency=from_currency, to_currency=to_currency, amount=amount)
    resp, status = exchange_currency(
        user_id=user_id,
        from_currency=str(from_currency),
        to_currency=(None if to_currency is None else str(to_currency)),
        amount=amount,
    )
    return jsonify(resp), status
