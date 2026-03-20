"""
事件引擎 - Events Engine

分层随机事件系统，让世界有"呼吸感"。
- 微事件(MICRO)：每次操作可触发，轻量反馈
- 小事件(MINOR)：每天5-15个，探索核心
- 中事件(MAJOR)：每周2-3个，支线任务
- 大事件(WORLD)：每月1-2个，世界事件
- 史诗事件(EPIC)：天劫/飞升等里程碑

本模块只做"选事件 + 算效果"，不碰数据库。
调用方拿到返回的 effect dict 后自行落库。
"""

from __future__ import annotations

import random
from enum import Enum
from copy import deepcopy
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 事件层级枚举
# ---------------------------------------------------------------------------

class EventTier(Enum):
    MICRO = "micro"      # 微事件
    MINOR = "minor"      # 小事件
    MAJOR = "major"      # 中事件
    WORLD = "world"      # 大事件/世界事件
    EPIC = "epic"        # 史诗事件(天劫/飞升)


# ---------------------------------------------------------------------------
# 触发类型常量
# ---------------------------------------------------------------------------

TRIGGER_CULTIVATION = "cultivation"
TRIGGER_EXPLORATION = "exploration"
TRIGGER_COMBAT = "combat"
TRIGGER_TRAVEL = "travel"


# ===========================================================================
# 微事件池
# ===========================================================================

# --- 修炼微事件 (15个) ---------------------------------------------------

CULTIVATION_MICRO_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "bird_song",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 30,
        "text": "修炼间隙，一只灵雀落在窗棂上，清脆鸣叫驱散了些许疲惫。",
        "effect": {"mentality": 1},
        "condition": {"map": "luoxia_valley"},
        "choices": None,
    },
    {
        "id": "spirit_fluctuation",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 25,
        "text": "远处传来一阵灵力波动，似有同道正在突破，你心生感悟。",
        "effect": {"mentality": 2},
        "condition": None,
        "choices": None,
    },
    {
        "id": "pearl_glow",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 10,
        "text": "鸿蒙珠在识海中微微发光，一缕玄奥道韵沁入神魂。",
        "effect": {"dao_heng": 1},
        "condition": {"min_realm": 10},  # 金丹以上
        "choices": None,
    },
    {
        "id": "fellow_disciple",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 20,
        "text": "传来消息，同门师兄弟成功突破！宗门上下一片欢腾，你也深受鼓舞。",
        "effect": {"exp": 10},
        "condition": {"has_sect": True},
        "choices": None,
    },
    {
        "id": "rain_spirit",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 15,
        "text": "天降灵雨，灵气浓度骤增！你抓住机会疯狂吸纳，修炼效率倍增。",
        "effect": {"cultivation_multiplier": 2.0},
        "condition": {"random": 0.03},
        "choices": None,
    },
    {
        "id": "heart_demon_whisper",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 18,
        "text": "入定之际，一道阴冷的声音在耳畔低语，心魔蠢蠢欲动。",
        "effect": {"mentality": -3},
        "condition": None,
        "choices": None,
    },
    {
        "id": "ancient_text",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 12,
        "text": "翻阅旧物时发现一页古籍残篇，上面记载的功法心得令你颇有启发。",
        "effect": {"skill_proficiency": 5},
        "condition": None,
        "choices": None,
    },
    {
        "id": "spirit_vein_pulse",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 15,
        "text": "脚下灵脉猛然跳动了一下，充沛的灵气涌入体内。",
        "effect": {"exp": 20},
        "condition": None,
        "choices": None,
    },
    {
        "id": "meditation_deep",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 20,
        "text": "你进入了前所未有的深度入定状态，心境空明澄澈。",
        "effect": {"mentality": 3},
        "condition": None,
        "choices": None,
    },
    {
        "id": "qi_deviation_near",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 8,
        "text": "修炼中灵气逆行，差点走火入魔！虽然惊险化解，但体内留下了些许隐患——不过这次经历也带来了宝贵的领悟。",
        "effect": {"mentality": -5, "exp": 30},
        "condition": None,
        "choices": None,
    },
    {
        "id": "moonlight_bath",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 16,
        "text": "月华如水洒落，温柔地浸润全身经脉，伤势缓缓恢复。",
        "effect": {"hp_recover_pct": 0.05},
        "condition": None,
        "choices": None,
    },
    {
        "id": "wind_whisper",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 22,
        "text": "清风拂过耳畔，似乎在低语着什么……你隐约感应到远方有一处机缘。",
        "effect": {"hint": True},
        "condition": None,
        "choices": None,
    },
    {
        "id": "earth_pulse",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 14,
        "text": "大地灵脉与你的气息产生共鸣，一股浑厚的力量暂时强化了你的体魄。",
        "effect": {"defense_buff_pct": 0.05, "buff_duration": 600},
        "condition": None,
        "choices": None,
    },
    {
        "id": "star_alignment",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 10,
        "text": "夜空中星辰排列成奇异图案，你望着星图若有所悟，对天道的理解更深了一分。",
        "effect": {"dao_yan": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "karma_echo",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_CULTIVATION,
        "weight": 10,
        "text": "冥冥中感应到一丝因果波动，过往的杀伐果断在此刻凝为逆天之志。",
        "effect": {"dao_ni": 1},
        "condition": None,
        "choices": None,
    },
]

# --- 探索微事件 (15个) ---------------------------------------------------

EXPLORATION_MICRO_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "footprints",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 20,
        "text": "地面上出现一串奇怪的脚印，似乎是某种灵兽留下的。",
        "effect": {},
        "condition": None,
        "choices": [
            {"label": "追踪", "effect": {"trigger_encounter": "random_beast"}},
            {"label": "忽略", "effect": {}},
        ],
    },
    {
        "id": "herb_discovery",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 25,
        "text": "路边发现一株不起眼的灵草，散发着淡淡灵气。",
        "effect": {"item_random_herb": True},
        "condition": None,
        "choices": None,
    },
    {
        "id": "ancient_stone",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 15,
        "text": "一块布满苔藓的远古石碑立在路旁，上面刻着晦涩的符文。你仔细辨认，有所领悟。",
        "effect": {"exp": 15, "dao_random": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "trapped_spirit_beast",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 15,
        "text": "前方传来一阵悲鸣，一只小灵兽被陷阱困住，正在挣扎。",
        "effect": {},
        "condition": None,
        "choices": [
            {"label": "救助", "effect": {"mentality": 2, "affinity_beast": 5}},
            {"label": "无视", "effect": {}},
        ],
    },
    {
        "id": "hidden_cave",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 12,
        "text": "树丛后面隐约露出一个洞口，里面黑漆漆的，不知通向何方。",
        "effect": {},
        "condition": None,
        "choices": [
            {"label": "探索", "effect": {"trigger_encounter": "cave_random"}},
            {"label": "离开", "effect": {}},
        ],
    },
    {
        "id": "merchant_encounter",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 18,
        "text": "一个背着巨大箱子的行商向你招手：\"道友，看看有没有需要的？\"",
        "effect": {},
        "condition": None,
        "choices": [
            {"label": "交易", "effect": {"open_shop": "wandering_merchant"}},
            {"label": "婉拒", "effect": {}},
        ],
    },
    {
        "id": "broken_formation",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 14,
        "text": "脚下泥土中露出一角阵旗，这里似乎有一座残破的阵法。",
        "effect": {},
        "condition": None,
        "choices": [
            {"label": "研究", "effect": {"skill_formation_proficiency": 3, "exp": 10}},
            {"label": "跳过", "effect": {}},
        ],
    },
    {
        "id": "spirit_fruit_tree",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 16,
        "text": "路旁一棵灵果树上挂着几颗熟透的灵果，散发诱人香气。",
        "effect": {"item": "spirit_fruit", "quantity": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "mirage",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 10,
        "text": "眼前景象忽然扭曲变幻，亭台楼阁凭空出现——是蜃楼幻境！",
        "effect": {"mentality_check": True},
        "condition": None,
        "choices": None,
    },
    {
        "id": "old_battlefield",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 14,
        "text": "踏入一片古战场遗迹，残刀断剑散落各处，空气中仍弥漫着淡淡的杀伐之气。",
        "effect": {"item_random_equip_fragment": True},
        "condition": None,
        "choices": None,
    },
    {
        "id": "mountain_spring",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 20,
        "text": "山涧中发现一处灵泉，泉水清冽甘甜，饮下后灵力缓缓恢复。",
        "effect": {"mp_recover_pct": 0.10},
        "condition": None,
        "choices": None,
    },
    {
        "id": "fog_maze",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 10,
        "text": "浓雾突然弥漫四周，辨不清方向。需要靠神识探路。",
        "effect": {"perception_check": True},
        "condition": None,
        "choices": None,
    },
    {
        "id": "falling_star",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 5,
        "text": "一颗流星划过夜空，拖着璀璨的尾焰坠入远处山谷！",
        "effect": {"item": "meteorite_iron", "quantity": 1},
        "condition": {"random": 0.02},
        "choices": None,
    },
    {
        "id": "npc_in_danger",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 12,
        "text": "前方传来呼救声，一名散修正被妖兽追赶。",
        "effect": {},
        "condition": None,
        "choices": [
            {"label": "救助", "effect": {"mentality": 3, "exp": 15, "reputation": 5}},
            {"label": "旁观", "effect": {"mentality": -1}},
        ],
    },
    {
        "id": "strange_sound",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_EXPLORATION,
        "weight": 18,
        "text": "密林深处传来诡异的声响，忽远忽近，令人心生不安。",
        "effect": {},
        "condition": None,
        "choices": [
            {"label": "调查", "effect": {"trigger_encounter": "mystery_sound"}},
            {"label": "远离", "effect": {}},
        ],
    },
]

# --- 战斗微事件 (10个) ---------------------------------------------------

COMBAT_MICRO_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "rage_burst",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 20,
        "text": "怒火在胸中燃烧，你爆发出惊人的力量！",
        "effect": {"attack_buff_pct": 0.10, "buff_duration": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "calm_focus",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 18,
        "text": "心如止水，万物归寂。你的出手变得精准无比。",
        "effect": {"crit_rate_buff": 0.05, "buff_duration": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "terrain_advantage",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 15,
        "text": "你抢占了有利地形，背靠山崖，进退自如。",
        "effect": {"defense_buff_pct": 0.10, "buff_duration": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "weapon_glow",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 12,
        "text": "手中法器突然爆发出璀璨光芒，附加了一层元素之力！",
        "effect": {"extra_element_damage": True, "buff_duration": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "enemy_hesitate",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 14,
        "text": "敌人似乎在犹豫，露出了一瞬间的破绽！",
        "effect": {"free_turn": True},
        "condition": None,
        "choices": None,
    },
    {
        "id": "spirit_shield_auto",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 10,
        "text": "危急时刻，体内灵力自发凝聚成一面灵盾，挡住了致命一击！",
        "effect": {"absorb_hit": True},
        "condition": None,
        "choices": None,
    },
    {
        "id": "breakthrough_battle",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 8,
        "text": "以战养战！殊死搏斗中，你对武道的理解更深了一层。",
        "effect": {"exp_multiplier": 1.5},
        "condition": None,
        "choices": None,
    },
    {
        "id": "dao_resonance",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 10,
        "text": "你所修之道在战斗中产生共鸣，天地灵气为你所用。",
        "effect": {"dao_random": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "mercy_kill",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 16,
        "text": "你干净利落地结束了战斗，没有造成不必要的痛苦。仁者之心，天道可鉴。",
        "effect": {"mentality": 1},
        "condition": None,
        "choices": None,
    },
    {
        "id": "bloodlust",
        "tier": EventTier.MICRO,
        "trigger": TRIGGER_COMBAT,
        "weight": 8,
        "text": "鲜血的气息刺激了你的嗜杀本能，力量暴涨的同时，心境也出现了裂痕。",
        "effect": {"attack_buff_pct": 0.20, "mentality": -2, "buff_duration": 1},
        "condition": None,
        "choices": None,
    },
]


# ===========================================================================
# 事件池索引
# ===========================================================================

# 所有微事件合并后按 trigger 分组，供快速查找
_ALL_MICRO_EVENTS: List[Dict[str, Any]] = (
    CULTIVATION_MICRO_EVENTS
    + EXPLORATION_MICRO_EVENTS
    + COMBAT_MICRO_EVENTS
)

# trigger -> [events]  预编译索引
_EVENTS_BY_TRIGGER: Dict[str, List[Dict[str, Any]]] = {}
for _evt in _ALL_MICRO_EVENTS:
    _EVENTS_BY_TRIGGER.setdefault(_evt["trigger"], []).append(_evt)


# ===========================================================================
# 条件检查
# ===========================================================================

def check_event_condition(
    event: Dict[str, Any],
    player_data: Dict[str, Any],
    map_id: Optional[str] = None,
) -> bool:
    """检查事件是否满足触发条件。

    condition 为 None 表示无条件触发。
    condition 为 dict 时，所有键必须同时满足（AND 逻辑）。

    支持的条件键:
        map          - 必须在指定地图
        min_realm    - 玩家境界 >= 此值
        max_realm    - 玩家境界 <= 此值
        has_sect     - 玩家必须有宗门
        dao_min      - 道途最低值，如 {"heng": 30}
        random       - 额外概率过滤 (0~1)
    """
    cond = event.get("condition")
    if not cond:
        return True

    def _to_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)

    def _to_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    # 地图限制
    if "map" in cond:
        if map_id != cond["map"]:
            return False

    # 境界范围
    realm_id = _to_int(player_data.get("realm_id", 1), 1)
    if "min_realm" in cond and realm_id < _to_int(cond.get("min_realm"), 0):
        return False
    if "max_realm" in cond and realm_id > _to_int(cond.get("max_realm"), 10**9):
        return False

    # 宗门
    if cond.get("has_sect"):
        if not player_data.get("sect_id"):
            return False

    # 道途最低值
    dao_min = cond.get("dao_min")
    if dao_min and isinstance(dao_min, dict):
        for dao_key, min_val in dao_min.items():
            actual = _to_float(player_data.get(f"dao_{dao_key}", 0), 0.0)
            required = _to_float(min_val, 0.0)
            if actual < required:
                return False

    # 随机概率
    if "random" in cond:
        prob = max(0.0, min(1.0, _to_float(cond.get("random"), 0.0)))
        if random.random() > prob:
            return False

    return True


# ===========================================================================
# 事件选取
# ===========================================================================

def get_events_by_trigger(trigger: str) -> List[Dict[str, Any]]:
    """返回某触发类型的所有事件（深拷贝，防止外部修改污染池子）。"""
    return deepcopy(_EVENTS_BY_TRIGGER.get(trigger, []))


def roll_micro_event(
    trigger: str,
    player_data: Dict[str, Any],
    map_id: Optional[str] = None,
    *,
    base_trigger_rate: float = 0.35,
) -> Optional[Dict[str, Any]]:
    """根据触发类型、玩家数据、地图加权随机选择一个微事件。

    Args:
        trigger: 触发类型 (cultivation / exploration / combat / travel)
        player_data: 玩家数据字典，至少包含 realm_id
        map_id: 当前地图 ID，用于地图限定事件
        base_trigger_rate: 基础触发概率（默认 35%），先过这一关才选具体事件

    Returns:
        事件 dict 的深拷贝，或 None（未触发）
    """
    # 第一层：是否触发事件
    if random.random() > base_trigger_rate:
        return None

    # 第二层：筛选满足条件的事件
    candidates = _EVENTS_BY_TRIGGER.get(trigger, [])
    eligible: List[Dict[str, Any]] = []
    weights: List[float] = []

    for evt in candidates:
        if check_event_condition(evt, player_data, map_id):
            eligible.append(evt)
            weights.append(evt.get("weight", 10))

    if not eligible:
        return None

    # 第三层：加权随机
    chosen = random.choices(eligible, weights=weights, k=1)[0]
    return deepcopy(chosen)


# ===========================================================================
# 效果计算
# ===========================================================================

def apply_event_effect(
    event: Dict[str, Any],
    player_data: Dict[str, Any],
    choice_index: Optional[int] = None,
) -> Dict[str, Any]:
    """计算事件效果，返回变化字典。不修改 player_data，不写数据库。

    Args:
        event: 事件 dict
        player_data: 玩家当前数据（用于百分比计算等）
        choice_index: 如果事件有 choices，指定玩家选择的索引

    Returns:
        changes dict，调用方按需应用。示例::

            {
                "mentality": 3,        # 心境变化
                "exp": 20,             # 经验变化
                "hp_recover": 150,     # 实际回血量
                "attack_buff_pct": 0.1,# 攻击百分比 buff
                "buff_duration": 600,  # buff 持续秒数
                "items": [{"item_id": "spirit_fruit", "quantity": 1}],
                ...
            }
    """
    changes: Dict[str, Any] = {}

    # 确定最终 effect：直接 effect 或 choice 里的 effect
    effect = _resolve_effect(event, choice_index)
    if not effect:
        return changes

    # --- 直传属性 ---
    # 数值型属性直接搬运
    _DIRECT_KEYS = (
        "mentality", "exp", "dao_heng", "dao_yan", "dao_ni",
        "dao_random", "skill_proficiency", "skill_formation_proficiency",
        "reputation", "affinity_beast",
        "cultivation_multiplier", "exp_multiplier",
        "attack_buff_pct", "defense_buff_pct", "crit_rate_buff",
        "buff_duration",
    )
    for key in _DIRECT_KEYS:
        if key in effect:
            changes[key] = effect[key]

    # --- 百分比恢复：转换为绝对值 ---
    if "hp_recover_pct" in effect:
        max_hp = player_data.get("max_hp", player_data.get("hp", 100))
        changes["hp_recover"] = int(max_hp * effect["hp_recover_pct"])

    if "mp_recover_pct" in effect:
        max_mp = player_data.get("max_mp", player_data.get("mp", 50))
        changes["mp_recover"] = int(max_mp * effect["mp_recover_pct"])

    # --- 物品产出 ---
    if "item" in effect:
        changes.setdefault("items", []).append({
            "item_id": effect["item"],
            "quantity": effect.get("quantity", 1),
        })

    # --- 标志型 effect（由调用方自行解读） ---
    _FLAG_KEYS = (
        "hint", "mentality_check", "perception_check",
        "extra_element_damage", "free_turn", "absorb_hit",
        "trigger_encounter", "open_shop",
        "item_random_herb", "item_random_equip_fragment",
    )
    for key in _FLAG_KEYS:
        if key in effect:
            changes[key] = effect[key]

    return changes


def _resolve_effect(
    event: Dict[str, Any],
    choice_index: Optional[int],
) -> Dict[str, Any]:
    """从事件中提取最终生效的 effect。

    无选项事件直接返回 event["effect"]。
    有选项事件根据 choice_index 返回对应选项的 effect；
    若 choice_index 无效，默认取第一个选项。
    """
    choices = event.get("choices")
    base_effect = event.get("effect") or {}

    if not choices:
        return base_effect

    if choice_index is not None and 0 <= choice_index < len(choices):
        choice_effect = choices[choice_index].get("effect", {})
    else:
        # 无有效选择时默认第一个选项
        choice_effect = choices[0].get("effect", {})

    # 合并：基础 effect + 选项 effect，选项优先
    merged = {**base_effect, **choice_effect}
    return merged


# ===========================================================================
# 工具函数
# ===========================================================================

def get_all_micro_events() -> List[Dict[str, Any]]:
    """返回全部微事件的深拷贝列表。"""
    return deepcopy(_ALL_MICRO_EVENTS)


def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
    """按 ID 查找单个微事件。"""
    for evt in _ALL_MICRO_EVENTS:
        if evt["id"] == event_id:
            return deepcopy(evt)
    return None


def get_event_choices_text(event: Dict[str, Any]) -> List[str]:
    """提取事件的选项文本列表，供 UI 层使用。无选项返回空列表。"""
    choices = event.get("choices")
    if not choices:
        return []
    return [c.get("label", f"选项{i+1}") for i, c in enumerate(choices)]
