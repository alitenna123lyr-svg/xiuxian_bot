"""Gacha routes."""

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
from core.services.gacha_service import list_banners, get_pity, pull_gacha, get_gacha_status


gacha_bp = Blueprint("gacha", __name__)


def _parse_bool_strict(value, *, default: bool = False):
    if value is None:
        return default, None
    if isinstance(value, bool):
        return value, None
    if isinstance(value, int):
        if value in (0, 1):
            return bool(value), None
        return None, "布尔参数仅支持 true/false 或 0/1"
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True, None
        if text in {"0", "false", "no", "n", "off"}:
            return False, None
        return None, "布尔参数仅支持 true/false 或 0/1"
    return None, "布尔参数类型无效"


@gacha_bp.route("/api/gacha/banners", methods=["GET"])
def gacha_banners():
    banners = list_banners()
    return success(banners=banners)


@gacha_bp.route("/api/gacha/pity/<user_id>", methods=["GET"])
def gacha_pity(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    banner_id = request.args.get("banner_id")
    if banner_id is None:
        return error("MISSING_PARAMS", "Missing banner_id", 400)
    try:
        banner_id = int(banner_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid banner_id", 400)
    return success(pity=get_pity(user_id, banner_id))


@gacha_bp.route("/api/gacha/status/<user_id>", methods=["GET"])
def gacha_status(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    return success(status=get_gacha_status(user_id))


@gacha_bp.route("/api/gacha/pull", methods=["POST"])
def gacha_pull():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    banner_id = data.get("banner_id")
    count = data.get("count", 1)
    request_id = data.get("request_id")
    force_paid, bool_error = _parse_bool_strict(data.get("force_paid"), default=False)
    if bool_error:
        return error("INVALID", bool_error, 400)
    log_action("gacha_pull", user_id=user_id, request_id=request_id, banner_id=banner_id, count=count, force_paid=force_paid)
    if banner_id is None:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    try:
        banner_id = int(banner_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid banner_id", 400)
    try:
        count = int(count or 1)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid count", 400)
    resp, http_status = pull_gacha(user_id, banner_id, count=count, force_paid=force_paid, request_id=request_id)
    return jsonify(resp), http_status
