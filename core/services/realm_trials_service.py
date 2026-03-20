from __future__ import annotations

import time
from typing import Any, Dict, Optional

from core.database.connection import fetch_one, execute, db_transaction
from core.game.realm_trials import get_realm_trial_def


def get_realm_trial(user_id: str, rank: int) -> Optional[Dict[str, Any]]:
    trial_def = get_realm_trial_def(rank)
    if not trial_def:
        return None
    row = fetch_one(
        "SELECT * FROM user_realm_trials WHERE user_id = %s AND realm_id = %s",
        (user_id, int(rank or 1)),
    )
    if row:
        return dict(row)
    return {
        "user_id": user_id,
        "realm_id": int(rank or 1),
        "hunt_target": int(trial_def.get("hunt_target", 0) or 0),
        "hunt_progress": 0,
        "secret_target": int(trial_def.get("secret_target", 0) or 0),
        "secret_progress": 0,
        "completed": 0,
        "completed_at": 0,
        "updated_at": 0,
    }


def get_or_create_realm_trial(user_id: str, rank: int) -> Optional[Dict[str, Any]]:
    trial_def = get_realm_trial_def(rank)
    if not trial_def:
        return None
    existing = fetch_one(
        "SELECT * FROM user_realm_trials WHERE user_id = %s AND realm_id = %s",
        (user_id, int(rank or 1)),
    )
    if existing:
        return dict(existing)
    now = int(time.time())
    execute(
        """INSERT INTO user_realm_trials
           (user_id, realm_id, hunt_target, hunt_progress, secret_target, secret_progress, completed, completed_at, updated_at)
           VALUES (%s, %s, %s, 0, %s, 0, 0, 0, %s)
           ON CONFLICT (user_id, realm_id) DO NOTHING""",
        (user_id, int(rank or 1), int(trial_def.get("hunt_target", 0) or 0), int(trial_def.get("secret_target", 0) or 0), now),
    )
    row = fetch_one(
        "SELECT * FROM user_realm_trials WHERE user_id = %s AND realm_id = %s",
        (user_id, int(rank or 1)),
    )
    return dict(row) if row else None


def is_realm_trial_complete(user_id: str, rank: int) -> bool:
    trial_def = get_realm_trial_def(rank)
    if not trial_def:
        return True
    row = get_or_create_realm_trial(user_id, rank)
    if not row:
        return True
    return int(row.get("completed", 0) or 0) == 1


def increment_realm_trial(user_id: str, rank: int, kind: str, amount: int = 1) -> Optional[Dict[str, Any]]:
    trial_def = get_realm_trial_def(rank)
    if not trial_def:
        return None
    kind = (kind or "").strip().lower()
    if kind not in ("hunt", "secret"):
        return None
    now = int(time.time())
    inc = max(0, int(amount or 0))
    if inc <= 0:
        row = fetch_one(
            "SELECT * FROM user_realm_trials WHERE user_id = %s AND realm_id = %s",
            (user_id, int(rank or 1)),
        )
        return dict(row) if row else get_realm_trial(user_id, rank)
    with db_transaction() as cur:
        cur.execute(
            """INSERT INTO user_realm_trials
               (user_id, realm_id, hunt_target, hunt_progress, secret_target, secret_progress, completed, completed_at, updated_at)
               VALUES (%s, %s, %s, 0, %s, 0, 0, 0, %s)
               ON CONFLICT (user_id, realm_id) DO NOTHING""",
            (user_id, int(rank or 1), int(trial_def.get("hunt_target", 0) or 0), int(trial_def.get("secret_target", 0) or 0), now),
        )
        cur.execute(
            "SELECT * FROM user_realm_trials WHERE user_id = %s AND realm_id = %s FOR UPDATE",
            (user_id, int(rank or 1)),
        )
        row = cur.fetchone()
        if not row:
            return None
        hunt_progress = int(row["hunt_progress"] or 0)
        secret_progress = int(row["secret_progress"] or 0)
        hunt_target = int(row["hunt_target"] or 0)
        secret_target = int(row["secret_target"] or 0)
        if kind == "hunt":
            hunt_progress = min(hunt_target, hunt_progress + inc)
        else:
            secret_progress = min(secret_target, secret_progress + inc)
        completed = 1 if (hunt_progress >= hunt_target and secret_progress >= secret_target) else 0
        completed_at = int(row["completed_at"] or 0)
        if completed and completed_at == 0:
            completed_at = now
        cur.execute(
            """UPDATE user_realm_trials
               SET hunt_progress = %s, secret_progress = %s, completed = %s, completed_at = %s, updated_at = %s
               WHERE id = %s
               RETURNING user_id, realm_id, hunt_target, secret_target, hunt_progress, secret_progress, completed, completed_at""",
            (hunt_progress, secret_progress, completed, completed_at, now, row["id"]),
        )
        updated = cur.fetchone()
        if not updated:
            return None
        return dict(updated)
