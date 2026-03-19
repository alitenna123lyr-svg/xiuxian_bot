"""Audit log routes."""

from flask import Blueprint, jsonify, request

from core.config import config
from core.routes._helpers import error, resolve_actor_path_user_id
from core.services.audit_log_service import list_audit_logs


audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/api/audit/logs/<user_id>", methods=["GET"])
def audit_logs_for_user(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    module = request.args.get("module")
    limit = request.args.get("limit", 100)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid limit", 400)
    return jsonify(list_audit_logs(user_id=user_id, module=module, limit=limit))


@audit_bp.route("/api/audit/logs", methods=["GET"])
def audit_logs_admin():
    token = str(request.headers.get("X-Internal-Token", "") or "")
    if not token or token != str(config.internal_api_token or ""):
        return error("UNAUTHORIZED", "Invalid internal token", 401)
    user_id = request.args.get("user_id")
    module = request.args.get("module")
    limit = request.args.get("limit", 100)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid limit", 400)
    return jsonify(list_audit_logs(user_id=user_id, module=module, limit=limit))
