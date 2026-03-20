"""Event and world boss routes."""

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.services.events_service import (
    get_active_events,
    get_event_status,
    claim_event_reward,
    get_world_boss_status,
    attack_world_boss,
    exchange_event_points,
)


events_bp = Blueprint("events", __name__)


@events_bp.route("/api/events", methods=["GET"])
def events_list():
    return success(events=get_active_events())


@events_bp.route("/api/events/status/<user_id>", methods=["GET"])
def events_status(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    return jsonify(get_event_status(user_id))


@events_bp.route("/api/events/claim", methods=["POST"])
def events_claim():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    event_id = data.get("event_id")
    log_action("event_claim", user_id=user_id, event_id=event_id)
    if not event_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = claim_event_reward(user_id, event_id)
    return jsonify(resp), http_status


@events_bp.route("/api/events/exchange", methods=["POST"])
def events_exchange():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    event_id = data.get("event_id")
    exchange_id = data.get("exchange_id")
    raw_quantity = data.get("quantity", 1)
    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        return error("INVALID_PARAMS", "quantity 必须是整数且大于 0", 400)
    if quantity <= 0:
        return error("INVALID_PARAMS", "quantity 必须是整数且大于 0", 400)
    if not event_id or not exchange_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    log_action("event_exchange", user_id=user_id, event_id=event_id, exchange_id=exchange_id, quantity=quantity)
    resp, http_status = exchange_event_points(user_id, event_id, exchange_id, quantity=quantity)
    return jsonify(resp), http_status


@events_bp.route("/api/worldboss/status", methods=["GET"])
def worldboss_status():
    return jsonify(get_world_boss_status())


@events_bp.route("/api/worldboss/attack", methods=["POST"])
def worldboss_attack():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    log_action("worldboss_attack", user_id=user_id)
    resp, http_status = attack_world_boss(user_id)
    return jsonify(resp), http_status
