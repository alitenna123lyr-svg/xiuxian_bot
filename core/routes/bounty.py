"""Global bounty routes."""

from flask import Blueprint, jsonify, request

from core.routes._helpers import error, log_action, parse_json_payload, resolve_actor_user_id
from core.services.bounty_service import publish_bounty, list_bounties, accept_bounty, submit_bounty


bounty_bp = Blueprint("bounty", __name__)


@bounty_bp.route("/api/bounties", methods=["GET"])
def bounty_list():
    status = request.args.get("status", "open")
    limit = request.args.get("limit", 30)
    resp, http_status = list_bounties(status=status, limit=limit)
    return jsonify(resp), http_status


@bounty_bp.route("/api/bounty/publish", methods=["POST"])
def bounty_publish():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    wanted_item_id = data.get("wanted_item_id")
    wanted_quantity = data.get("wanted_quantity")
    reward_spirit_low = data.get("reward_spirit_low")
    description = data.get("description", "")
    if not wanted_item_id or wanted_quantity is None or reward_spirit_low is None:
        return error("MISSING_PARAMS", "Missing wanted_item_id/wanted_quantity/reward_spirit_low", 400)
    log_action(
        "bounty_publish",
        user_id=user_id,
        wanted_item_id=wanted_item_id,
        wanted_quantity=wanted_quantity,
        reward_spirit_low=reward_spirit_low,
    )
    resp, http_status = publish_bounty(
        user_id=user_id,
        wanted_item_id=str(wanted_item_id),
        wanted_quantity=wanted_quantity,
        reward_spirit_low=reward_spirit_low,
        description=str(description or ""),
    )
    return jsonify(resp), http_status


@bounty_bp.route("/api/bounty/accept", methods=["POST"])
def bounty_accept():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    bounty_id = data.get("bounty_id")
    if bounty_id is None:
        return error("MISSING_PARAMS", "Missing bounty_id", 400)
    try:
        bounty_id = int(bounty_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid bounty_id", 400)
    log_action("bounty_accept", user_id=user_id, bounty_id=bounty_id)
    resp, http_status = accept_bounty(user_id=user_id, bounty_id=bounty_id)
    return jsonify(resp), http_status


@bounty_bp.route("/api/bounty/submit", methods=["POST"])
def bounty_submit():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    bounty_id = data.get("bounty_id")
    if bounty_id is None:
        return error("MISSING_PARAMS", "Missing bounty_id", 400)
    try:
        bounty_id = int(bounty_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid bounty_id", 400)
    log_action("bounty_submit", user_id=user_id, bounty_id=bounty_id)
    resp, http_status = submit_bounty(user_id=user_id, bounty_id=bounty_id)
    return jsonify(resp), http_status
