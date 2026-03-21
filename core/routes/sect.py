"""Sect (guild) routes."""

from flask import Blueprint, request, jsonify
from pathlib import Path
from typing import Any, Dict, List

from core.routes._helpers import (
    error,
    success,
    log_action,
    parse_json_payload,
    resolve_actor_path_user_id,
    resolve_actor_user_id,
)
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from core.services.sect_service import (
    create_sect,
    create_branch_request,
    list_sects,
    get_sect_detail,
    join_sect,
    leave_sect,
    promote_member,
    transfer_leadership,
    kick_member,
    donate,
    get_quests,
    claim_quest,
    get_user_sect,
    get_user_sect_buffs,
    challenge_war,
    join_branch,
    review_branch_request,
)


sect_bp = Blueprint("sect", __name__)


STORY_SECTS_FALLBACK: List[Dict[str, Any]] = [
    {
        "sect_id": "tianyuan_sect",
        "name": "天元宗",
        "alignment": "正道",
        "specialty": "综合型宗门，传承完整",
        "leader": "宗主（化神后期）",
        "notable": "主角所在宗门，陈长老为主角恩师",
        "display_order": 1,
    },
    {
        "sect_id": "taiching_sect",
        "name": "太清宗",
        "alignment": "正道",
        "specialty": "恒道传承，底蕴深厚",
        "leader": "太清掌教（大乘期）",
        "notable": "柳清竹叛逃处，太初曾潜伏于此",
        "display_order": 2,
    },
    {
        "sect_id": "tianjian_sect",
        "name": "天剑门",
        "alignment": "正道",
        "specialty": "剑道极致",
        "leader": "剑主（大乘期）",
        "notable": "楚千殇所属，万剑峰为标志性区域",
        "display_order": 3,
    },
    {
        "sect_id": "danding_pavilion",
        "name": "丹鼎阁",
        "alignment": "中立",
        "specialty": "丹道至尊",
        "leader": "丹圣（化神圆满）",
        "notable": "天下丹药三成出自此处",
        "display_order": 4,
    },
    {
        "sect_id": "nixian_temple",
        "name": "逆天殿",
        "alignment": "邪道（后转中立）",
        "specialty": "逆道修行，逆天改命",
        "leader": "殿主（大乘期）",
        "notable": "王逆为少主，天元盟约后转型为中立势力",
        "display_order": 5,
    },
    {
        "sect_id": "xingchen_pavilion",
        "name": "星辰阁",
        "alignment": "中立",
        "specialty": "星象占卜，天道感知",
        "leader": "星璇（万年星辰意志）",
        "notable": "隐世势力，极少参与世俗纷争",
        "display_order": 6,
    },
    {
        "sect_id": "xuesha_sect",
        "name": "血煞宗（已覆灭）",
        "alignment": "邪道",
        "specialty": "血道修行，以战养战",
        "leader": "已阵亡",
        "notable": "卷三被正道联盟剿灭",
        "display_order": 7,
    },
]


def _story_volume_path() -> Path:
    return Path(__file__).resolve().parents[2] / "texts" / "story" / "volumes" / "volume_10_encyclopedia.yaml"


def _load_story_fixed_sects() -> List[Dict[str, Any]]:
    if yaml is None:
        return [dict(row) for row in STORY_SECTS_FALLBACK]

    try:
        raw = yaml.safe_load(_story_volume_path().read_text(encoding="utf-8"))
    except Exception:
        return [dict(row) for row in STORY_SECTS_FALLBACK]

    volume = (raw or {}).get("volume_10") if isinstance(raw, dict) else None
    sects = (volume or {}).get("sects", {}) if isinstance(volume, dict) else {}
    entries = sects.get("entries", {}) if isinstance(sects, dict) else {}
    if not isinstance(entries, dict) or not entries:
        return [dict(row) for row in STORY_SECTS_FALLBACK]

    result: List[Dict[str, Any]] = []
    for idx, (sect_id, item) in enumerate(entries.items(), start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or sect_id)
        alignment = str(item.get("alignment") or "中立")
        specialty = str(item.get("specialty") or "")
        leader = str(item.get("leader") or "")
        notable = str(item.get("notable") or "")
        desc = "｜".join(x for x in (alignment, specialty, notable) if x)
        result.append({
            "sect_id": str(sect_id),
            "name": name,
            "alignment": alignment,
            "specialty": specialty,
            "leader": leader,
            "notable": notable,
            "description": desc,
            "display_order": idx,
        })

    return result or [dict(row) for row in STORY_SECTS_FALLBACK]


def _merge_story_with_runtime(story_rows: List[Dict[str, Any]], runtime_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    runtime_by_name = {str(row.get("name") or ""): row for row in runtime_rows}

    merged: List[Dict[str, Any]] = []
    for row in story_rows:
        name = str(row.get("name") or "")
        runtime = runtime_by_name.get(name)

        item = dict(row)
        item["is_story_fixed"] = True
        item.setdefault("description", "｜".join(x for x in (item.get("alignment"), item.get("specialty"), item.get("notable")) if x))

        if runtime:
            item["runtime_sect_id"] = runtime.get("sect_id")
            item["level"] = int(runtime.get("level", runtime.get("sect_level", 1)) or 1)
            item["exp"] = int(runtime.get("exp", 0) or 0)
            item["max_members"] = int(runtime.get("max_members", 0) or 0)
            item["branch_count"] = int(runtime.get("branch_count", 0) or 0)
        else:
            item.setdefault("level", 1)
            item.setdefault("exp", 0)
            item.setdefault("max_members", 0)
            item.setdefault("branch_count", 0)

        merged.append(item)

    return merged


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


@sect_bp.route("/api/sect/create", methods=["POST"])
def sect_create():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    name = data.get("name")
    description = data.get("description", "")
    log_action("sect_create", user_id=user_id, name=name)
    if not name:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = create_sect(user_id, name, description)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/list", methods=["GET"])
def sect_list():
    raw_limit = request.args.get("limit", 20)
    keyword = (request.args.get("keyword") or "").strip()
    fixed_only = (request.args.get("fixed_only", "1") or "1").strip().lower() in ("1", "true", "yes", "on")

    try:
        limit = max(1, min(int(raw_limit or 20), 100))
    except (TypeError, ValueError):
        limit = 20

    runtime_entries = list_sects(limit=max(limit, 50), keyword=keyword or None)
    story_entries = _load_story_fixed_sects()
    merged_story = _merge_story_with_runtime(story_entries, runtime_entries)

    if keyword:
        k = keyword.lower()

        def _match_story(row: Dict[str, Any]) -> bool:
            return any(k in str(row.get(field, "")).lower() for field in ("name", "alignment", "specialty", "leader", "notable", "description"))

        merged_story = [row for row in merged_story if _match_story(row)]

    if fixed_only:
        return success(sects=merged_story[:limit], source="story_fixed")

    story_names = {str(row.get("name") or "") for row in merged_story}
    extras = [row for row in runtime_entries if str(row.get("name") or "") not in story_names]
    return success(sects=(merged_story + extras)[:limit], source="story_plus_runtime")


@sect_bp.route("/api/sect/<sect_id>", methods=["GET"])
def sect_detail(sect_id: str):
    data = get_sect_detail(sect_id)
    if not data:
        return error("NOT_FOUND", "Sect not found", 404)
    return success(sect=data)


@sect_bp.route("/api/sect/member/<user_id>", methods=["GET"])
def sect_member(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    data = get_user_sect(user_id)
    if not data:
        return error("NOT_FOUND", "Not in sect", 404)
    return success(sect=data)


@sect_bp.route("/api/sect/buffs/<user_id>", methods=["GET"])
def sect_buffs(user_id: str):
    _, auth_error = resolve_actor_path_user_id(user_id)
    if auth_error:
        return auth_error
    return success(buffs=get_user_sect_buffs(user_id))


@sect_bp.route("/api/sect/join", methods=["POST"])
def sect_join():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    sect_id = data.get("sect_id")
    log_action("sect_join", user_id=user_id, sect_id=sect_id)
    if not sect_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = join_sect(user_id, sect_id)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/leave", methods=["POST"])
def sect_leave():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    log_action("sect_leave", user_id=user_id)
    resp, http_status = leave_sect(user_id)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/promote", methods=["POST"])
def sect_promote():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    target_user_id = data.get("target_user_id")
    role = data.get("role", "member")
    log_action("sect_promote", user_id=user_id, target_user_id=target_user_id, role=role)
    if not target_user_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = promote_member(user_id, target_user_id, role)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/transfer", methods=["POST"])
def sect_transfer():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    target_user_id = data.get("target_user_id")
    log_action("sect_transfer", user_id=user_id, target_user_id=target_user_id)
    if not target_user_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = transfer_leadership(user_id, target_user_id)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/kick", methods=["POST"])
def sect_kick():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    target_user_id = data.get("target_user_id")
    log_action("sect_kick", user_id=user_id, target_user_id=target_user_id)
    if not target_user_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = kick_member(user_id, target_user_id)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/donate", methods=["POST"])
def sect_donate():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    raw_copper = data.get("copper", 0)
    raw_gold = data.get("gold", 0)
    try:
        copper = int(raw_copper or 0)
        gold = int(raw_gold or 0)
    except (TypeError, ValueError):
        return error("INVALID_AMOUNT", "捐献数量必须是整数", 400)
    log_action("sect_donate", user_id=user_id, copper=copper, gold=gold)
    resp, http_status = donate(user_id, copper=copper, gold=gold)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/quests/<sect_id>", methods=["GET"])
def sect_quests(sect_id: str):
    user_id = request.args.get("user_id")
    if user_id:
        _, auth_error = resolve_actor_path_user_id(user_id)
        if auth_error:
            return auth_error
    resp, http_status = get_quests(sect_id, user_id=user_id)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/quests/claim", methods=["POST"])
def sect_quests_claim():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    quest_id = data.get("quest_id")
    log_action("sect_quest_claim", user_id=user_id, quest_id=quest_id)
    if quest_id is None:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    try:
        quest_id = int(quest_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid quest_id", 400)
    resp, http_status = claim_quest(user_id, quest_id)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/war/challenge", methods=["POST"])
def sect_war():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    target_sect_id = data.get("target_sect_id")
    log_action("sect_war", user_id=user_id, target_sect_id=target_sect_id)
    if not target_sect_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = challenge_war(user_id, target_sect_id)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/branch/request", methods=["POST"])
def sect_branch_request():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    name = data.get("name")
    description = data.get("description", "")
    log_action("sect_branch_request", user_id=user_id, name=name)
    if not name:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = create_branch_request(user_id, name, description)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/branch/join", methods=["POST"])
def sect_branch_join():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    branch_id = data.get("branch_id")
    log_action("sect_branch_join", user_id=user_id, branch_id=branch_id)
    if not branch_id:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    resp, http_status = join_branch(user_id, branch_id)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/branch/review", methods=["POST"])
def sect_branch_review():
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    request_id = data.get("request_id")
    approve, bool_error = _parse_bool_strict(data.get("approve"), default=False)
    if bool_error:
        return error("INVALID", bool_error, 400)
    log_action("sect_branch_review", user_id=user_id, request_id=request_id, approve=approve)
    if request_id is None:
        return error("MISSING_PARAMS", "Missing parameters", 400)
    try:
        request_id = int(request_id)
    except (TypeError, ValueError):
        return error("INVALID", "Invalid request_id", 400)
    resp, http_status = review_branch_request(user_id, request_id, approve)
    return jsonify(resp), http_status


@sect_bp.route("/api/sect/daily_claim", methods=["POST"])
def sect_daily_claim():
    """宗门每日资源领取（替代原签到系统）。

    资源多少取决于宗门等级、大方程度、是否压榨弟子。
    每日只能领取一次。
    """
    data, payload_error = parse_json_payload()
    if payload_error:
        return payload_error
    user_id, auth_error = resolve_actor_user_id(data)
    if auth_error:
        return auth_error
    log_action("sect_daily_claim", user_id=user_id)

    from core.database.connection import fetch_one, execute_query, db_transaction
    import datetime
    import json

    today = datetime.date.today()

    # 查玩家宗门
    member = fetch_one(
        "SELECT sect_id, role, daily_claimed FROM sect_members WHERE player_id = %s",
        (user_id,)
    )
    if not member:
        return jsonify({"success": False, "message": "你尚未加入任何宗门"}), 400

    if member.get("daily_claimed") and str(member["daily_claimed"]) == str(today):
        return jsonify({"success": False, "message": "今日已领取宗门资源，明日再来"}), 400

    # 查宗门定义
    sect = fetch_one(
        "SELECT * FROM sect_definitions WHERE sect_id = %s",
        (member["sect_id"],)
    )
    if not sect:
        return jsonify({"success": False, "message": "宗门数据异常"}), 500

    # 计算资源
    level = int(sect.get("sect_level", 1) or 1)
    generosity = float(sect.get("generosity", 0.5) or 0.5)
    oppression = float(sect.get("oppression", 0.0) or 0.0)

    base_copper = int(sect.get("daily_copper", 100) or 100)
    base_exp = int(sect.get("daily_exp", 50) or 50)

    # 等级加成 (每级+10%)
    level_mult = 1.0 + (level - 1) * 0.10
    # 大方程度加成 (0.5=正常, 1.0=翻倍)
    gen_mult = 0.5 + generosity

    final_copper = int(base_copper * level_mult * gen_mult)
    final_exp = int(base_exp * level_mult * gen_mult)

    # 压榨：资源额外+50%但扣心境
    mentality_cost = 0
    if oppression > 0:
        final_copper = int(final_copper * (1 + oppression * 0.5))
        final_exp = int(final_exp * (1 + oppression * 0.5))
        mentality_cost = int(oppression * 5)

    # 物品发放
    daily_items_json = sect.get("daily_items", "[]") or "[]"
    try:
        daily_items = json.loads(daily_items_json) if isinstance(daily_items_json, str) else daily_items_json
    except Exception:
        daily_items = []

    # 事务：发放资源 + 标记已领取
    with db_transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET copper = copper + %s, exp = exp + %s WHERE user_id = %s",
            (final_copper, final_exp, user_id)
        )
        if mentality_cost > 0:
            cur.execute(
                "UPDATE users SET mentality = GREATEST(0, mentality - %s) WHERE user_id = %s",
                (mentality_cost, user_id)
            )
        cur.execute(
            "UPDATE sect_members SET daily_claimed = %s WHERE player_id = %s",
            (today, user_id)
        )

    rewards = {
        "copper": final_copper,
        "exp": final_exp,
        "items": daily_items,
        "mentality_cost": mentality_cost,
    }
    return jsonify({"success": True, "rewards": rewards}), 200
