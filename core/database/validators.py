"""
core/database/validators.py
数据库列名/表名白名单验证，防止 SQL 注入。
"""

import re
from typing import Set

# ── 各表允许的列名白名单 ──

USERS_COLUMNS: Set[str] = {
    "user_id", "in_game_username", "lang", "state", "exp", "rank",
    "dy_times", "copper", "gold", "spirit_high", "spirit_exquisite", "spirit_supreme",
    "immortal_flawed", "immortal_low", "immortal_mid", "immortal_high", "immortal_supreme",
    "asc_reduction", "sign", "element",
    "hp", "mp", "max_hp", "max_mp", "attack", "defense", "crit_rate",
    "weak_until", "breakthrough_pity", "created_at",
    "last_sign_timestamp", "consecutive_sign_days", "max_signin_days",
    "secret_realm_attempts", "secret_realm_last_reset",
    "equipped_weapon", "equipped_armor", "equipped_accessory1", "equipped_accessory2",
    "last_hunt_time", "hunts_today", "hunts_today_reset",
    "last_secret_time", "last_quest_claim_time", "last_enhance_time",
    "cultivation_boost_until", "cultivation_boost_pct", "realm_drop_boost_until", "breakthrough_protect_until",
    "attack_buff_until", "attack_buff_value", "defense_buff_until", "defense_buff_value",
    "breakthrough_boost_until", "breakthrough_boost_pct",
    "telegram_id",
    "pvp_rating", "pvp_wins", "pvp_losses", "pvp_draws",
    "pvp_daily_count", "pvp_daily_reset", "pvp_season_id",
    "stamina", "stamina_updated_at", "vitals_updated_at",
    "chat_energy_today", "chat_energy_reset",
    "gacha_free_today", "gacha_paid_today", "gacha_daily_reset",
    "daily_cultivate_stone_day", "daily_cultivate_stone_claimed",
    "secret_loot_score", "alchemy_output_score",
}

ITEMS_COLUMNS: Set[str] = {
    "id", "user_id", "item_id", "item_name", "item_type", "quality",
    "quantity", "level", "attack_bonus", "defense_bonus",
    "hp_bonus", "mp_bonus", "enhance_level",
    "first_round_reduction_pct", "crit_heal_pct", "element_damage_pct", "low_hp_shield_pct",
}

TIMINGS_COLUMNS: Set[str] = {
    "id", "user_id", "start_time", "type", "base_gain",
}

BATTLE_LOGS_COLUMNS: Set[str] = {
    "id", "user_id", "monster_id", "victory", "rounds",
    "exp_gained", "copper_gained", "gold_gained", "timestamp",
}

USER_SKILLS_COLUMNS: Set[str] = {
    "id", "user_id", "skill_id", "equipped", "learned_at",
}

USER_QUESTS_COLUMNS: Set[str] = {
    "id", "user_id", "quest_id", "progress", "goal", "claimed", "assigned_date",
}

# 表名 -> 列集合 映射
TABLE_COLUMNS = {
    "users": USERS_COLUMNS,
    "items": ITEMS_COLUMNS,
    "timings": TIMINGS_COLUMNS,
    "battle_logs": BATTLE_LOGS_COLUMNS,
    "user_skills": USER_SKILLS_COLUMNS,
    "user_quests": USER_QUESTS_COLUMNS,
}

# 合法平台名
VALID_PLATFORMS: Set[str] = {"telegram"}

# 合法表名（允许通过 database_query API 查询的表）
VALID_TABLES: Set[str] = {"users", "items", "timings"}

# 安全标识符正则（仅允许字母、数字、下划线）
_SAFE_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


class ColumnValidationError(ValueError):
    """列名验证失败异常"""
    pass


def validate_column(column: str, table: str = "users") -> str:
    """
    验证列名是否在白名单中。
    返回验证后的列名（原值），不在白名单则抛出异常。
    """
    if not isinstance(column, str) or not _SAFE_IDENTIFIER_RE.match(column):
        raise ColumnValidationError(f"Invalid column name format: {column!r}")

    allowed = TABLE_COLUMNS.get(table)
    if allowed is None:
        raise ColumnValidationError(f"Unknown table: {table!r}")

    if column not in allowed:
        raise ColumnValidationError(
            f"Column {column!r} is not allowed for table {table!r}. "
            f"Allowed: {sorted(allowed)}"
        )
    return column


def validate_columns(columns: list, table: str = "users") -> list:
    """批量验证列名列表"""
    return [validate_column(c, table) for c in columns]


def validate_platform(platform: str) -> str:
    """验证平台名"""
    if platform not in VALID_PLATFORMS:
        raise ColumnValidationError(
            f"Invalid platform: {platform!r}. Allowed: {sorted(VALID_PLATFORMS)}"
        )
    return platform


def validate_table(table_name: str) -> str:
    """验证表名"""
    if table_name not in VALID_TABLES:
        raise ColumnValidationError(
            f"Invalid table name: {table_name!r}. Allowed: {sorted(VALID_TABLES)}"
        )
    return table_name
