from __future__ import annotations

"""路由层公共工具函数。"""

import json
import logging
from typing import Any

from flask import jsonify, request

logger = logging.getLogger("core.server")


def error(code: str, message: str, http_status: int = 400, **extra):
    payload = {"success": False, "code": code, "message": message}
    payload.update(extra)
    return jsonify(payload), http_status


def success(**data):
    payload = {"success": True}
    payload.update(data)
    return jsonify(payload)


def parse_json_payload() -> tuple[dict[str, Any] | None, tuple[Any, int] | None]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, error("INVALID_PAYLOAD", "Invalid JSON payload", 400)
    return payload, None


def resolve_actor_user_id(payload: dict[str, Any] | None) -> tuple[str | None, tuple[Any, int] | None]:
    actor_user_id = str(request.headers.get("X-Actor-User-Id", "") or "").strip()
    body_user_id = str((payload or {}).get("user_id", "") or "").strip()

    if not actor_user_id:
        return None, error("UNAUTHORIZED", "Missing actor identity", 401)
    if body_user_id and body_user_id != actor_user_id:
        return None, error("FORBIDDEN", "user_id does not match actor identity", 403)
    return actor_user_id, None


def resolve_actor_path_user_id(path_user_id: str) -> tuple[str | None, tuple[Any, int] | None]:
    return resolve_actor_user_id({"user_id": path_user_id})


def log_action(event: str, user_id: str = "", request_id: str | None = None,
               delta: dict | None = None, result: str | None = None, **fields):
    payload = {
        "action": event,
        "user_id": str(user_id) if user_id is not None else "",
        "request_id": request_id,
        "delta": delta,
        "result": result,
        **fields,
    }
    try:
        logger.info(json.dumps(payload, ensure_ascii=False))
        try:
            from core.services.audit_log_service import write_audit_log
            write_audit_log(
                module=str(event or "core").split("_")[0],
                action=str(event or ""),
                user_id=str(user_id or ""),
                success=(result or "") != "error",
                detail=payload,
            )
        except Exception:
            pass
    except Exception as exc:
        context_fields = []
        for key in ("request_id", "session_id", "monster_id", "realm_id", "item_id", "skill_id"):
            value = payload.get(key)
            if value not in (None, "", []):
                context_fields.append(f"{key}={value}")
        context = " ".join(context_fields) if context_fields else "context=none"
        logger.warning(
            "log_action_serialize_failed action=%s user_id=%s error=%s %s",
            event,
            str(user_id or ""),
            type(exc).__name__,
            context,
        )
