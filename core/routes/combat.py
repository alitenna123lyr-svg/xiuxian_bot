"""战斗 / 狩猎 / 秘境路由。"""

import time

from flask import Blueprint, request, jsonify

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_user_id,
    resolve_actor_path_user_id,
)
from core.config import config
from core.database.connection import get_user_by_id, update_user
from core.game.combat import get_available_monsters
from core.game.realms import REALMS, ELEMENT_BONUSES
from core.game.secret_realms import (
    get_available_secret_realms,
    get_secret_realm_attempts_left,
)
from core.services.settlement import settle_hunt, settle_secret_realm_explore
from core.services.turn_battle_service import (
    start_hunt_session,
    action_hunt_session,
    start_secret_realm_session,
    action_secret_session,
)
from core.utils.timeutil import midnight_timestamp

combat_bp = Blueprint("combat", __name__)


def _parse_bool_param(value, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off", ""}:
            return False
    return default


def _check_secret_realm_daily_reset(user_id: str, user: dict) -> dict:
    """Reset secret realm attempts if the stored reset timestamp is from a previous day."""
    now = int(time.time())
    last_reset = int(user.get("secret_realm_last_reset", 0) or 0)
    if last_reset < midnight_timestamp():
        update_user(user_id, {
            "secret_realm_attempts": 0,
            "secret_realm_last_reset": now,
        })
        return get_user_by_id(user_id)
    return user


@combat_bp.route("/api/hunt", methods=["POST"])
def hunt():
    """狩猎 API"""
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    monster_id = data.get("monster_id")
    use_active = _parse_bool_param(data.get("use_active"), default=True)
    active_skill_id = data.get("active_skill_id")
    request_id = data.get("request_id")
    log_action("hunt", user_id=user_id, request_id=request_id,
               monster_id=monster_id, use_active=use_active)

    if not user_id or not monster_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)

    resp, http_status = settle_hunt(
        user_id=user_id,
        monster_id=monster_id,
        request_id=request_id,
        hunt_cooldown_seconds=config.hunt_cooldown,
        use_active=use_active,
        active_skill_id=active_skill_id,
    )
    return jsonify(resp), http_status


@combat_bp.route("/api/monsters", methods=["GET"])
def list_monsters():
    """获取可挑战的怪物列表（按当前地图筛选，以修为量化难度）"""
    user_id = request.args.get("user_id")

    if user_id:
        user = get_user_by_id(user_id)
        if not user:
            return error("ERROR", "User not found", 404)
        rank = user.get("rank", 1)
        current_map = str(user.get("current_map") or "")
    else:
        rank = 1
        current_map = ""

    from core.game.maps import get_map
    map_info = get_map(current_map) if current_map else None
    map_name = map_info.get("name", current_map) if map_info else ""

    monsters = get_available_monsters(rank, current_map=current_map)
    return success(
        monsters=monsters,
        user_rank=rank,
        current_map=current_map,
        current_map_name=map_name,
    )


@combat_bp.route("/api/hunt/status/<user_id>", methods=["GET"])
def hunt_status(user_id: str):
    """狩猎冷却状态"""
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    user = get_user_by_id(user_id)
    if not user:
        return error("ERROR", "User not found", 404)
    now = int(time.time())
    last_hunt = int(user.get("last_hunt_time", 0) or 0)
    remaining = config.hunt_cooldown - (now - last_hunt)
    remaining = max(0, int(remaining))
    return success(
        cooldown_remaining=remaining,
        can_hunt=remaining <= 0,
    )


@combat_bp.route("/api/hunt/turn/start", methods=["POST"])
def hunt_turn_start():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    monster_id = data.get("monster_id")
    log_action("hunt_turn_start", user_id=user_id, monster_id=monster_id)
    if not user_id or not monster_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = start_hunt_session(user_id, monster_id)
    return jsonify(resp), http_status


@combat_bp.route("/api/hunt/turn/action", methods=["POST"])
def hunt_turn_action():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    session_id = data.get("session_id")
    action = data.get("action", "normal")
    skill_id = data.get("skill_id")
    request_id = data.get("request_id")
    log_action("hunt_turn_action", user_id=user_id, session_id=session_id, request_id=request_id, skill_id=skill_id, action_type=action)
    if not user_id or not session_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = action_hunt_session(user_id, session_id, action=action, skill_id=skill_id, request_id=request_id)
    return jsonify(resp), http_status


@combat_bp.route("/api/realms", methods=["GET"])
def list_realms():
    """获取所有境界"""
    return success(realms=REALMS, elements=ELEMENT_BONUSES)


@combat_bp.route("/api/secret-realms/<user_id>", methods=["GET"])
def secret_realms_list(user_id):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    user = get_user_by_id(user_id)
    if not user:
        return error("ERROR", "User not found", 404)

    user = _check_secret_realm_daily_reset(user_id, user)

    realms = get_available_secret_realms(user.get("rank", 1))
    return success(
        attempts_left=get_secret_realm_attempts_left(user),
        realms=realms,
    )


@combat_bp.route("/api/secret-realms/explore", methods=["POST"])
def secret_realms_explore():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    realm_id = data.get("realm_id")
    request_id = data.get("request_id")
    path = data.get("path")
    multi_step = _parse_bool_param(data.get("multi_step"), default=False)
    multi_step_nodes = data.get("multi_step_nodes")
    log_action("secret_realm_explore", user_id=user_id, request_id=request_id,
               realm_id=realm_id, path=path, multi_step=multi_step, multi_step_nodes=multi_step_nodes)

    if not user_id or not realm_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)

    resp, http_status = settle_secret_realm_explore(
        user_id=user_id,
        realm_id=realm_id,
        path=path,
        multi_step=multi_step,
        multi_step_nodes=multi_step_nodes,
        request_id=request_id,
        secret_cooldown_seconds=config.secret_realm_cooldown,
    )
    return jsonify(resp), http_status


@combat_bp.route("/api/secret-realms/turn/start", methods=["POST"])
def secret_realms_turn_start():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    realm_id = data.get("realm_id")
    path = data.get("path")
    interactive = _parse_bool_param(data.get("interactive"), default=False)
    log_action("secret_realm_turn_start", user_id=user_id, realm_id=realm_id, path=path)
    if not user_id or not realm_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = start_secret_realm_session(
        user_id,
        realm_id,
        path,
        secret_cooldown_seconds=config.secret_realm_cooldown,
        interactive=interactive,
    )
    return jsonify(resp), http_status


@combat_bp.route("/api/secret-realms/turn/action", methods=["POST"])
def secret_realms_turn_action():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    session_id = data.get("session_id")
    action = data.get("action", "normal")
    skill_id = data.get("skill_id")
    choice = data.get("choice")
    request_id = data.get("request_id")
    log_action("secret_realm_turn_action", user_id=user_id, session_id=session_id, request_id=request_id, action_type=action, skill_id=skill_id)
    if not user_id or not session_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = action_secret_session(
        user_id,
        session_id,
        action=action,
        skill_id=skill_id,
        choice=choice,
        request_id=request_id,
    )
    return jsonify(resp), http_status
