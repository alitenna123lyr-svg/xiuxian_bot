"""Detailed audit logging service."""

from __future__ import annotations

import json
import time
from typing import Any, Dict

from core.database.connection import execute, fetch_all


def write_audit_log(
    *,
    module: str,
    action: str,
    user_id: str = "",
    target_user_id: str = "",
    success: bool = True,
    detail: Dict[str, Any] | None = None,
) -> None:
    payload = detail or {}
    execute(
        """
        INSERT INTO audit_logs (module, action, user_id, target_user_id, success, detail_json, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(module or ""),
            str(action or ""),
            str(user_id or ""),
            str(target_user_id or ""),
            1 if success else 0,
            json.dumps(payload, ensure_ascii=False),
            int(time.time()),
        ),
    )


def list_audit_logs(*, user_id: str | None = None, module: str | None = None, limit: int = 100) -> Dict[str, Any]:
    lim = max(1, min(500, int(limit or 100)))
    if user_id and module:
        rows = fetch_all(
            "SELECT * FROM audit_logs WHERE user_id = %s AND module = %s ORDER BY id DESC LIMIT %s",
            (str(user_id), str(module), lim),
        )
    elif user_id:
        rows = fetch_all(
            "SELECT * FROM audit_logs WHERE user_id = %s ORDER BY id DESC LIMIT %s",
            (str(user_id), lim),
        )
    elif module:
        rows = fetch_all(
            "SELECT * FROM audit_logs WHERE module = %s ORDER BY id DESC LIMIT %s",
            (str(module), lim),
        )
    else:
        rows = fetch_all("SELECT * FROM audit_logs ORDER BY id DESC LIMIT %s", (lim,))
    return {"success": True, "logs": [dict(row) for row in rows]}
