"""
世界地图与区域系统 - World Map & Region System

七层世界架构：凡界 -> 灵界 -> 真界 -> 仙界 -> 神界 -> 造化宇宙 -> 鸿蒙本源
每层世界包含多个洲/域，每个洲/域下设若干具体区域（地图）。
玩家根据境界、三道值等条件解锁新区域。
"""

from typing import Dict, Any, Optional, List


# ---------------------------------------------------------------------------
# 世界层级定义
# ---------------------------------------------------------------------------

WORLD_TIERS = [
    {"tier": 1, "name": "凡界", "desc": "灵气稀薄，天材地宝稀少", "max_realm": 21},
    {"tier": 2, "name": "灵界", "desc": "灵气浓郁百倍于凡界", "max_realm": 31},
    {"tier": 3, "name": "真界", "desc": "法则可感可触", "max_realm": 32},
    {"tier": 4, "name": "仙界", "desc": "四大天域，法则主题各异"},
    {"tier": 5, "name": "神界", "desc": "以神道立身"},
    {"tier": 6, "name": "造化宇宙", "desc": "开辟独立宇宙的层次"},
    {"tier": 7, "name": "鸿蒙本源", "desc": "回归三道本源，超越天道"},
]

# 按 tier 快查
_TIER_BY_ID: Dict[int, Dict[str, Any]] = {t["tier"]: t for t in WORLD_TIERS}


# ---------------------------------------------------------------------------
# 地图定义
# ---------------------------------------------------------------------------

MAPS: Dict[str, Dict[str, Any]] = {

    # =======================================================================
    #  凡界 - 苍澜洲 (tier 1, region: canglan)
    # =======================================================================

    "canglan_city": {
        "id": "canglan_city",
        "name": "苍澜城",
        "world_tier": 1,
        "region": "canglan",
        "region_name": "苍澜洲",
        "desc": "主角出生地，散修横行的边陲小城",
        "spirit_density": 1.0,
        "min_realm": 1,
        "unlock_condition": None,  # 起始区域，无条件
        "event_pool": {
            "combat": 30,
            "treasure": 15,
            "npc": 25,
            "story": 10,
            "puzzle": 5,
            "nothing": 15,
        },
        "monsters": ["wild_boar", "wolf", "spirit_rat"],
        "npcs": ["old_beggar", "merchant_wang", "herb_girl"],
        "adjacent": ["east_forest", "south_market", "north_mountain"],
    },

    "east_forest": {
        "id": "east_forest",
        "name": "东郊灵林",
        "world_tier": 1,
        "region": "canglan",
        "region_name": "苍澜洲",
        "desc": "苍澜城外东侧密林，灵兽出没，适合新手历练",
        "spirit_density": 1.05,
        "min_realm": 1,
        "unlock_condition": None,
        "event_pool": {
            "combat": 40,
            "treasure": 20,
            "npc": 10,
            "story": 5,
            "puzzle": 5,
            "nothing": 20,
        },
        "monsters": ["spirit_rat", "green_snake", "wild_boar", "shadow_fox"],
        "npcs": ["wandering_hunter"],
        "adjacent": ["canglan_city", "fallen_star_lake", "luoxia_valley"],
    },

    "south_market": {
        "id": "south_market",
        "name": "南市坊市",
        "world_tier": 1,
        "region": "canglan",
        "region_name": "苍澜洲",
        "desc": "苍澜城南侧繁华坊市，修士云集，丹药法器琳琅满目",
        "spirit_density": 0.9,  # 人多灵气薄
        "min_realm": 1,
        "unlock_condition": None,
        "event_pool": {
            "combat": 10,
            "treasure": 10,
            "npc": 45,
            "story": 15,
            "puzzle": 5,
            "nothing": 15,
        },
        "monsters": ["pickpocket_rat"],
        "npcs": ["merchant_wang", "auction_host_li", "appraiser_zhao", "pill_seller_sun"],
        "adjacent": ["canglan_city", "canglan_mines"],
    },

    "north_mountain": {
        "id": "north_mountain",
        "name": "北望灵山",
        "world_tier": 1,
        "region": "canglan",
        "region_name": "苍澜洲",
        "desc": "苍澜城北面灵山，山顶灵气充沛，乃修炼宝地",
        "spirit_density": 1.3,
        "min_realm": 2,  # 练气初期
        "unlock_condition": None,
        "event_pool": {
            "combat": 25,
            "treasure": 20,
            "npc": 15,
            "story": 15,
            "puzzle": 10,
            "nothing": 15,
        },
        "monsters": ["stone_ape", "cloud_crane", "mist_python"],
        "npcs": ["hermit_cultivator", "herb_girl"],
        "adjacent": ["canglan_city", "fallen_star_lake", "misty_swamp"],
    },

    "fallen_star_lake": {
        "id": "fallen_star_lake",
        "name": "坠星湖",
        "world_tier": 1,
        "region": "canglan",
        "region_name": "苍澜洲",
        "desc": "传说远古有星辰坠落于此，湖底隐藏秘境入口",
        "spirit_density": 1.15,
        "min_realm": 3,  # 练气中期
        "unlock_condition": None,
        "event_pool": {
            "combat": 25,
            "treasure": 25,
            "npc": 10,
            "story": 20,
            "puzzle": 10,
            "nothing": 10,
        },
        "monsters": ["lake_serpent", "water_spirit", "star_fragment_golem"],
        "npcs": ["mysterious_fisherman"],
        "adjacent": ["east_forest", "north_mountain"],
    },

    "luoxia_valley": {
        "id": "luoxia_valley",
        "name": "落霞谷",
        "world_tier": 1,
        "region": "canglan",
        "region_name": "苍澜洲",
        "desc": "霞光笼罩的幽谷，遍布灵草药田，丹修首选之地",
        "spirit_density": 1.1,
        "min_realm": 2,
        "unlock_condition": None,
        "event_pool": {
            "combat": 20,
            "treasure": 30,
            "npc": 15,
            "story": 10,
            "puzzle": 10,
            "nothing": 15,
        },
        "monsters": ["poison_bee", "flower_spider", "vine_demon"],
        "npcs": ["herb_elder_liu", "young_alchemist"],
        "adjacent": ["east_forest", "canglan_mines"],
    },

    "canglan_mines": {
        "id": "canglan_mines",
        "name": "苍澜矿脉",
        "world_tier": 1,
        "region": "canglan",
        "region_name": "苍澜洲",
        "desc": "地底纵横的灵石矿脉，盛产灵铁与晶石，亦有矿妖出没",
        "spirit_density": 0.95,
        "min_realm": 3,
        "unlock_condition": None,
        "event_pool": {
            "combat": 35,
            "treasure": 30,
            "npc": 5,
            "story": 5,
            "puzzle": 10,
            "nothing": 15,
        },
        "monsters": ["mine_rat", "crystal_golem", "shadow_bat", "earth_worm"],
        "npcs": ["miner_chief_zhang"],
        "adjacent": ["south_market", "luoxia_valley", "misty_swamp"],
    },

    "misty_swamp": {
        "id": "misty_swamp",
        "name": "瘴气沼泽",
        "world_tier": 1,
        "region": "canglan",
        "region_name": "苍澜洲",
        "desc": "终年瘴雾弥漫的险地，深处据说藏有上古传承",
        "spirit_density": 1.2,
        "min_realm": 5,  # 练气圆满
        "unlock_condition": None,
        "event_pool": {
            "combat": 45,
            "treasure": 15,
            "npc": 5,
            "story": 10,
            "puzzle": 10,
            "nothing": 15,
        },
        "monsters": ["swamp_toad", "miasma_ghost", "mud_golem", "poison_hydra"],
        "npcs": ["lost_scholar"],
        "adjacent": ["north_mountain", "canglan_mines"],
    },

    # =======================================================================
    #  凡界 - 天渊洲 (tier 1, region: tianyuan)  -- 筑基后解锁
    # =======================================================================

    "tianyuan_sect_city": {
        "id": "tianyuan_sect_city",
        "name": "天渊宗城",
        "world_tier": 1,
        "region": "tianyuan",
        "region_name": "天渊洲",
        "desc": "天渊洲最大的宗门城池，三大宗门环绕，秩序井然",
        "spirit_density": 1.4,
        "min_realm": 6,  # 筑基初期
        "unlock_condition": {"min_realm": 6},
        "event_pool": {
            "combat": 15,
            "treasure": 15,
            "npc": 35,
            "story": 20,
            "puzzle": 5,
            "nothing": 10,
        },
        "monsters": ["rogue_cultivator"],
        "npcs": ["sect_elder_chen", "mission_hall_deacon", "trade_pavilion_owner"],
        "adjacent": ["sword_peak", "pill_pavilion", "chaos_sea"],
    },

    "sword_peak": {
        "id": "sword_peak",
        "name": "剑锋山",
        "world_tier": 1,
        "region": "tianyuan",
        "region_name": "天渊洲",
        "desc": "天剑门祖庭，剑意纵横，凡人靠近即伤",
        "spirit_density": 1.5,
        "min_realm": 7,  # 筑基中期
        "unlock_condition": {"min_realm": 7},
        "event_pool": {
            "combat": 40,
            "treasure": 15,
            "npc": 15,
            "story": 15,
            "puzzle": 5,
            "nothing": 10,
        },
        "monsters": ["sword_puppet", "phantom_swordsman", "iron_winged_eagle"],
        "npcs": ["sword_master_ye"],
        "adjacent": ["tianyuan_sect_city", "demon_forest"],
    },

    "pill_pavilion": {
        "id": "pill_pavilion",
        "name": "丹鼎阁",
        "world_tier": 1,
        "region": "tianyuan",
        "region_name": "天渊洲",
        "desc": "天渊洲丹道圣地，万年药田环绕，丹香百里可闻",
        "spirit_density": 1.35,
        "min_realm": 6,
        "unlock_condition": {"min_realm": 6},
        "event_pool": {
            "combat": 10,
            "treasure": 30,
            "npc": 30,
            "story": 15,
            "puzzle": 10,
            "nothing": 5,
        },
        "monsters": ["pill_beast", "herb_guardian"],
        "npcs": ["grandmaster_dan", "pill_apprentice_mei"],
        "adjacent": ["tianyuan_sect_city", "demon_forest"],
    },

    "chaos_sea": {
        "id": "chaos_sea",
        "name": "乱星海",
        "world_tier": 1,
        "region": "tianyuan",
        "region_name": "天渊洲",
        "desc": "无主海域，散修、海盗、妖修三方交错，危机四伏",
        "spirit_density": 1.25,
        "min_realm": 8,  # 筑基后期
        "unlock_condition": {"min_realm": 8},
        "event_pool": {
            "combat": 40,
            "treasure": 20,
            "npc": 15,
            "story": 10,
            "puzzle": 5,
            "nothing": 10,
        },
        "monsters": ["sea_beast", "pirate_cultivator", "storm_spirit", "deep_kraken"],
        "npcs": ["pirate_king_hei", "island_hermit"],
        "adjacent": ["tianyuan_sect_city"],
    },

    "demon_forest": {
        "id": "demon_forest",
        "name": "妖兽森林",
        "world_tier": 1,
        "region": "tianyuan",
        "region_name": "天渊洲",
        "desc": "高阶妖兽盘踞之地，三阶以上妖兽随处可见，金丹以下勿入",
        "spirit_density": 1.6,
        "min_realm": 10,  # 金丹初期
        "unlock_condition": {"min_realm": 10},
        "event_pool": {
            "combat": 50,
            "treasure": 15,
            "npc": 5,
            "story": 10,
            "puzzle": 5,
            "nothing": 15,
        },
        "monsters": ["demon_tiger", "ancient_treant", "sky_roc", "blood_ape"],
        "npcs": ["beast_tamer_wu"],
        "adjacent": ["sword_peak", "pill_pavilion"],
    },

    # =======================================================================
    #  凡界 - 逆墟 (tier 1, region: nixu)  -- 化神期 + 逆道值>30%
    # =======================================================================

    "reverse_land": {
        "id": "reverse_land",
        "name": "逆墟荒原",
        "world_tier": 1,
        "region": "nixu",
        "region_name": "逆墟",
        "desc": "天道法则扭曲之地，逆修者的乐园，常人踏入即遭反噬",
        "spirit_density": 1.8,
        "min_realm": 18,  # 化神初期
        "unlock_condition": {"min_realm": 18, "dao_ni_pct": 30},
        "event_pool": {
            "combat": 35,
            "treasure": 15,
            "npc": 15,
            "story": 20,
            "puzzle": 10,
            "nothing": 5,
        },
        "monsters": ["reverse_wraith", "law_breaker", "chaos_elemental"],
        "npcs": ["reverse_dao_elder"],
        "adjacent": ["fate_crack", "ancient_battlefield"],
    },

    "fate_crack": {
        "id": "fate_crack",
        "name": "命运裂隙",
        "world_tier": 1,
        "region": "nixu",
        "region_name": "逆墟",
        "desc": "因果律崩塌的裂缝，窥探命运的代价是未知的反噬",
        "spirit_density": 2.0,
        "min_realm": 19,  # 化神中期
        "unlock_condition": {"min_realm": 19, "dao_ni_pct": 40},
        "event_pool": {
            "combat": 30,
            "treasure": 20,
            "npc": 10,
            "story": 25,
            "puzzle": 10,
            "nothing": 5,
        },
        "monsters": ["fate_phantom", "temporal_beast", "void_worm"],
        "npcs": ["fate_weaver"],
        "adjacent": ["reverse_land"],
    },

    "ancient_battlefield": {
        "id": "ancient_battlefield",
        "name": "远古战场",
        "world_tier": 1,
        "region": "nixu",
        "region_name": "逆墟",
        "desc": "上古大能陨落之地，残余法则交织，蕴含无上机缘与死劫",
        "spirit_density": 2.2,
        "min_realm": 20,  # 化神后期
        "unlock_condition": {"min_realm": 20, "dao_ni_pct": 50},
        "event_pool": {
            "combat": 40,
            "treasure": 20,
            "npc": 5,
            "story": 20,
            "puzzle": 10,
            "nothing": 5,
        },
        "monsters": ["ancient_war_spirit", "fallen_immortal_puppet", "abyssal_beast"],
        "npcs": ["ancient_will_fragment"],
        "adjacent": ["reverse_land"],
    },

    # =======================================================================
    #  凡界 - 星陨海 (tier 1, region: xingyun)  -- 元婴期 + 衍道值>30%
    # =======================================================================

    "star_fall_sea": {
        "id": "star_fall_sea",
        "name": "星陨之海",
        "world_tier": 1,
        "region": "xingyun",
        "region_name": "星陨海",
        "desc": "无尽星屑漂浮的虚空海域，蕴含推演天道的线索",
        "spirit_density": 1.7,
        "min_realm": 14,  # 元婴初期
        "unlock_condition": {"min_realm": 14, "dao_yan_pct": 30},
        "event_pool": {
            "combat": 25,
            "treasure": 25,
            "npc": 10,
            "story": 20,
            "puzzle": 15,
            "nothing": 5,
        },
        "monsters": ["star_jellyfish", "void_whale", "meteor_golem"],
        "npcs": ["star_gazer_elder"],
        "adjacent": ["ancient_ruins", "star_tower"],
    },

    "ancient_ruins": {
        "id": "ancient_ruins",
        "name": "上古遗迹",
        "world_tier": 1,
        "region": "xingyun",
        "region_name": "星陨海",
        "desc": "上古文明遗留的巨型建筑群，处处是阵法与禁制",
        "spirit_density": 1.9,
        "min_realm": 15,  # 元婴中期
        "unlock_condition": {"min_realm": 15, "dao_yan_pct": 40},
        "event_pool": {
            "combat": 30,
            "treasure": 20,
            "npc": 10,
            "story": 15,
            "puzzle": 20,
            "nothing": 5,
        },
        "monsters": ["ruin_guardian", "formation_spirit", "ancient_construct"],
        "npcs": ["ruin_scholar"],
        "adjacent": ["star_fall_sea"],
    },

    "star_tower": {
        "id": "star_tower",
        "name": "星辰塔",
        "world_tier": 1,
        "region": "xingyun",
        "region_name": "星陨海",
        "desc": "直入星河的高塔，每层蕴含不同法则试炼",
        "spirit_density": 2.5,
        "min_realm": 16,  # 元婴后期
        "unlock_condition": {"min_realm": 16, "dao_yan_pct": 50},
        "event_pool": {
            "combat": 35,
            "treasure": 15,
            "npc": 5,
            "story": 15,
            "puzzle": 25,
            "nothing": 5,
        },
        "monsters": ["star_trial_puppet", "law_fragment", "constellation_beast"],
        "npcs": ["tower_spirit"],
        "adjacent": ["star_fall_sea"],
    },

    # =======================================================================
    #  灵界 (tier 2, region: tianling / yao / xukong)  -- 渡劫飞升后
    # =======================================================================

    "tianling_domain": {
        "id": "tianling_domain",
        "name": "天灵域",
        "world_tier": 2,
        "region": "tianling",
        "region_name": "天灵域",
        "desc": "灵界主域，灵气浓郁百倍于凡界，仙人初入之地",
        "spirit_density": 100.0,
        "min_realm": 31,  # 渡劫期
        "unlock_condition": {"min_realm": 31},
        "event_pool": {
            "combat": 25,
            "treasure": 20,
            "npc": 25,
            "story": 15,
            "puzzle": 10,
            "nothing": 5,
        },
        "monsters": ["spirit_realm_beast"],
        "npcs": ["spirit_realm_guide"],
        "adjacent": ["yao_domain", "xukong_gorge"],
    },

    "yao_domain": {
        "id": "yao_domain",
        "name": "妖域",
        "world_tier": 2,
        "region": "yao",
        "region_name": "妖域",
        "desc": "灵界妖族领地，万妖之国，实力为尊",
        "spirit_density": 110.0,
        "min_realm": 31,
        "unlock_condition": {"min_realm": 31},
        "event_pool": {
            "combat": 45,
            "treasure": 15,
            "npc": 15,
            "story": 10,
            "puzzle": 5,
            "nothing": 10,
        },
        "monsters": ["demon_lord_minion", "ancient_demon_beast"],
        "npcs": ["demon_emperor_envoy"],
        "adjacent": ["tianling_domain"],
    },

    "xukong_gorge": {
        "id": "xukong_gorge",
        "name": "虚空裂谷",
        "world_tier": 2,
        "region": "xukong",
        "region_name": "虚空裂谷",
        "desc": "灵界与真界交界的虚空缝隙，空间法则紊乱",
        "spirit_density": 150.0,
        "min_realm": 32,  # 真仙
        "unlock_condition": {"min_realm": 32},
        "event_pool": {
            "combat": 35,
            "treasure": 25,
            "npc": 5,
            "story": 15,
            "puzzle": 15,
            "nothing": 5,
        },
        "monsters": ["void_creature", "space_ripper"],
        "npcs": ["void_wanderer"],
        "adjacent": ["tianling_domain"],
    },

    # =======================================================================
    #  真界 (tier 3) -- 占位
    # =======================================================================

    "zhen_realm_center": {
        "id": "zhen_realm_center",
        "name": "真界中枢",
        "world_tier": 3,
        "region": "zhen",
        "region_name": "真界",
        "desc": "法则可感可触的世界中心，待开放",
        "spirit_density": 500.0,
        "min_realm": 32,
        "unlock_condition": {"min_realm": 32},
        "event_pool": {"combat": 25, "treasure": 25, "npc": 20, "story": 20, "puzzle": 10, "nothing": 0},
        "monsters": [],
        "npcs": [],
        "adjacent": [],
    },

    # =======================================================================
    #  仙界 (tier 4) -- 占位
    # =======================================================================

    "xian_realm_center": {
        "id": "xian_realm_center",
        "name": "仙界中枢",
        "world_tier": 4,
        "region": "xian",
        "region_name": "仙界",
        "desc": "四大天域交汇之地，待开放",
        "spirit_density": 1000.0,
        "min_realm": 32,
        "unlock_condition": {"min_realm": 32},
        "event_pool": {"combat": 25, "treasure": 25, "npc": 20, "story": 20, "puzzle": 10, "nothing": 0},
        "monsters": [],
        "npcs": [],
        "adjacent": [],
    },

    # =======================================================================
    #  神界 (tier 5) -- 占位
    # =======================================================================

    "shen_realm_center": {
        "id": "shen_realm_center",
        "name": "神界中枢",
        "world_tier": 5,
        "region": "shen",
        "region_name": "神界",
        "desc": "以神道立身的世界，待开放",
        "spirit_density": 5000.0,
        "min_realm": 32,
        "unlock_condition": {"min_realm": 32},
        "event_pool": {"combat": 25, "treasure": 25, "npc": 20, "story": 20, "puzzle": 10, "nothing": 0},
        "monsters": [],
        "npcs": [],
        "adjacent": [],
    },

    # =======================================================================
    #  造化宇宙 (tier 6) -- 占位
    # =======================================================================

    "zaohua_center": {
        "id": "zaohua_center",
        "name": "造化宇宙中枢",
        "world_tier": 6,
        "region": "zaohua",
        "region_name": "造化宇宙",
        "desc": "开辟独立宇宙的层次，待开放",
        "spirit_density": 10000.0,
        "min_realm": 32,
        "unlock_condition": {"min_realm": 32},
        "event_pool": {"combat": 25, "treasure": 25, "npc": 20, "story": 20, "puzzle": 10, "nothing": 0},
        "monsters": [],
        "npcs": [],
        "adjacent": [],
    },

    # =======================================================================
    #  鸿蒙本源 (tier 7) -- 占位
    # =======================================================================

    "hongmeng_center": {
        "id": "hongmeng_center",
        "name": "鸿蒙本源",
        "world_tier": 7,
        "region": "hongmeng",
        "region_name": "鸿蒙本源",
        "desc": "回归三道本源，超越天道之境，待开放",
        "spirit_density": 99999.0,
        "min_realm": 32,
        "unlock_condition": {"min_realm": 32},
        "event_pool": {"combat": 25, "treasure": 25, "npc": 20, "story": 20, "puzzle": 10, "nothing": 0},
        "monsters": [],
        "npcs": [],
        "adjacent": [],
    },
}


# ---------------------------------------------------------------------------
# 预构建索引（启动时一次性构建，查询 O(1)）
# ---------------------------------------------------------------------------

_MAPS_BY_REGION: Dict[str, List[Dict[str, Any]]] = {}
_MAPS_BY_TIER: Dict[int, List[Dict[str, Any]]] = {}

for _map in MAPS.values():
    _MAPS_BY_REGION.setdefault(_map["region"], []).append(_map)
    _MAPS_BY_TIER.setdefault(_map["world_tier"], []).append(_map)


# ---------------------------------------------------------------------------
# 公开查询函数
# ---------------------------------------------------------------------------

def get_map(map_id: str) -> Optional[Dict[str, Any]]:
    """获取单个地图定义，不存在返回 None"""
    return MAPS.get(map_id)


def get_maps_by_region(region: str) -> List[Dict[str, Any]]:
    """获取指定区域（region）下的所有地图"""
    return list(_MAPS_BY_REGION.get(region, []))


def get_maps_by_tier(tier: int) -> List[Dict[str, Any]]:
    """获取指定世界层级下的所有地图"""
    return list(_MAPS_BY_TIER.get(tier, []))


def get_accessible_maps(
    realm_id: int,
    dao_heng: float = 0,
    dao_ni: float = 0,
    dao_yan: float = 0,
) -> List[Dict[str, Any]]:
    """
    根据玩家当前境界和三道值，返回所有可进入的地图列表。

    Args:
        realm_id: 当前境界 id（对应 realms.py 中 REALMS 的 id）
        dao_heng: 衡道百分比值 (0-100)
        dao_ni:   逆道百分比值 (0-100)
        dao_yan:  衍道百分比值 (0-100)

    Returns:
        可进入的地图字典列表
    """
    result = []
    for m in MAPS.values():
        # 境界门槛
        if realm_id < m["min_realm"]:
            continue

        cond = m.get("unlock_condition")
        if cond is None:
            result.append(m)
            continue

        # 检查 unlock_condition 中的各项门槛
        if realm_id < cond.get("min_realm", 0):
            continue
        if dao_ni < cond.get("dao_ni_pct", 0):
            continue
        if dao_yan < cond.get("dao_yan_pct", 0):
            continue
        if dao_heng < cond.get("dao_heng_pct", 0):
            continue

        result.append(m)
    return result


def get_adjacent_maps(map_id: str) -> List[Dict[str, Any]]:
    """获取与指定地图相邻的地图列表"""
    m = MAPS.get(map_id)
    if m is None:
        return []
    return [MAPS[adj] for adj in m.get("adjacent", []) if adj in MAPS]


def get_spirit_density(map_id: str) -> float:
    """获取指定地图的灵气浓度（修炼倍率），不存在返回 1.0"""
    m = MAPS.get(map_id)
    if m is None:
        return 1.0
    return m["spirit_density"]


def get_world_tier(tier: int) -> Optional[Dict[str, Any]]:
    """获取世界层级信息"""
    return _TIER_BY_ID.get(tier)


def get_all_regions() -> List[Dict[str, str]]:
    """
    返回所有不重复的区域摘要列表，按 world_tier 升序排列。
    每个元素: {"region": ..., "region_name": ..., "world_tier": ...}
    """
    seen = set()
    regions = []
    for m in MAPS.values():
        key = m["region"]
        if key not in seen:
            seen.add(key)
            regions.append({
                "region": m["region"],
                "region_name": m["region_name"],
                "world_tier": m["world_tier"],
            })
    regions.sort(key=lambda r: r["world_tier"])
    return regions


def format_world_map(current_map_id: str, realm_id: int,
                     dao_heng: float = 0, dao_ni: float = 0,
                     dao_yan: float = 0) -> str:
    """生成大地图文本，只显示玩家当前所在世界层级的地图。

    Args:
        current_map_id: 玩家当前所在地图ID
        realm_id: 玩家境界ID
        dao_heng/dao_ni/dao_yan: 三道亲和值

    Returns:
        格式化的大地图文本
    """
    current = MAPS.get(current_map_id)
    if not current:
        return "❌ 当前位置未知"

    current_tier = current["world_tier"]
    tier_info = _TIER_BY_ID.get(current_tier)
    tier_name = tier_info["name"] if tier_info else "未知"
    tier_desc = tier_info["desc"] if tier_info else ""

    # 获取当前世界层级的所有地图
    tier_maps = _MAPS_BY_TIER.get(current_tier, [])

    # 按区域分组
    regions: Dict[str, List[Dict[str, Any]]] = {}
    for m in tier_maps:
        regions.setdefault(m["region"], []).append(m)

    lines = [
        f"🗺️ 大地图 · {tier_name}",
        f"「{tier_desc}」",
        f"📍 当前位置：{current['name']}（{current.get('region_name', '')}）",
        "",
    ]

    for region_key, maps_in_region in regions.items():
        region_name = maps_in_region[0].get("region_name", region_key)
        lines.append(f"═══ {region_name} ═══")

        for m in maps_in_region:
            # 判断是否可进入
            accessible = realm_id >= m["min_realm"]
            cond = m.get("unlock_condition")
            if cond:
                if realm_id < cond.get("min_realm", 0):
                    accessible = False
                if dao_ni < cond.get("dao_ni_pct", 0):
                    accessible = False
                if dao_yan < cond.get("dao_yan_pct", 0):
                    accessible = False
                if dao_heng < cond.get("dao_heng_pct", 0):
                    accessible = False

            is_here = (m["id"] == current_map_id)
            if is_here:
                marker = "📍"
            elif accessible:
                marker = "✅"
            else:
                marker = "🔒"

            name = m["name"]
            density = m.get("spirit_density", 1.0)
            density_str = f"灵气×{density:.1f}" if density != 1.0 else ""

            if is_here:
                lines.append(f"  {marker} *{name}* ← 你在这里  {density_str}")
            elif accessible:
                adj = get_adjacent_maps(current_map_id)
                adj_ids = [a["id"] for a in adj]
                can_go = m["id"] in adj_ids
                go_str = "（可前往）" if can_go else ""
                lines.append(f"  {marker} {name}  {density_str} {go_str}")
            else:
                from core.game.realms import format_realm_display
                lines.append(f"  {marker} {name}  需{format_realm_display(m['min_realm'])}")

        lines.append("")

    # 显示相邻可前往的地图
    adj = get_adjacent_maps(current_map_id)
    if adj:
        lines.append("─── 可前往 ───")
        for a in adj:
            accessible = realm_id >= a["min_realm"]
            if accessible:
                lines.append(f"  → {a['name']}（{a.get('desc', '')[:20]}）")
            else:
                from core.game.realms import format_realm_display
                lines.append(f"  🔒 {a['name']}（需{format_realm_display(a['min_realm'])}）")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 区域移动系统
# ---------------------------------------------------------------------------

# 区域类型 → 可执行操作
_AREA_ACTIONS = {
    "city":     ["explore", "shop", "npc_talk", "quest", "sect_recruit"],
    "market":   ["shop", "auction", "npc_talk", "trade"],
    "forest":   ["explore", "hunt", "gather_herb"],
    "mountain": ["explore", "hunt", "cultivate_bonus", "gather_ore"],
    "lake":     ["explore", "hunt", "cultivate_bonus", "fish"],
    "mine":     ["explore", "gather_ore", "hunt"],
    "swamp":    ["explore", "hunt", "gather_herb"],
    "sect":     ["cultivate_bonus", "sect_daily", "npc_talk", "quest", "skill_learn"],
    "ruin":     ["explore", "hunt", "treasure_hunt"],
    "sea":      ["explore", "hunt", "treasure_hunt"],
    "secret":   ["explore", "hunt", "treasure_hunt", "boss"],
    "domain":   ["explore", "hunt", "cultivate_bonus"],
}

# 每个操作的显示名称
_ACTION_LABELS = {
    "explore":        "🗺️ 探索",
    "shop":           "🏪 商铺",
    "auction":        "🏛️ 万宝楼",
    "npc_talk":       "💬 交谈",
    "quest":          "📋 任务",
    "sect_recruit":   "🏛️ 宗门招聘",
    "trade":          "🤝 交易",
    "hunt":           "⚔️ 历练",
    "gather_herb":    "🌿 采药",
    "gather_ore":     "⛏️ 采矿",
    "fish":           "🎣 钓鱼",
    "cultivate_bonus":"🧘 灵地修炼",
    "sect_daily":     "📅 宗门领取",
    "skill_learn":    "📜 研读秘籍",
    "treasure_hunt":  "💎 寻宝",
    "boss":           "👹 挑战Boss",
}


def get_area_type(map_id: str) -> str:
    """推断区域类型（用于确定可执行操作）"""
    m = MAPS.get(map_id)
    if not m:
        return "forest"
    name = m.get("name", "")
    mid = m.get("id", "")

    if "city" in mid or "城" in name:
        return "city"
    if "market" in mid or "坊市" in name:
        return "market"
    if "forest" in mid or "林" in name or "密林" in name:
        return "forest"
    if "mountain" in mid or "山" in name or "峰" in name:
        return "mountain"
    if "lake" in mid or "湖" in name or "泽" in name:
        return "lake"
    if "mine" in mid or "矿" in name:
        return "mine"
    if "swamp" in mid or "沼" in name:
        return "swamp"
    if "sect" in mid or "宗" in name or "阁" in name or "门" in name or "谷" in name:
        return "sect"
    if "ruin" in mid or "废墟" in name or "遗迹" in name or "ruins" in mid:
        return "ruin"
    if "sea" in mid or "海" in name:
        return "sea"
    if "secret" in mid or "秘境" in name:
        return "secret"
    if "domain" in mid or "域" in name:
        return "domain"

    return "forest"


def get_area_actions(map_id: str) -> List[Dict[str, str]]:
    """返回当前区域可执行的操作列表

    Returns:
        [{"action": "explore", "label": "🗺️ 探索"}, ...]
    """
    area_type = get_area_type(map_id)
    actions = _AREA_ACTIONS.get(area_type, ["explore"])
    return [{"action": a, "label": _ACTION_LABELS.get(a, a)} for a in actions]


def calc_travel_cost(from_id: str, to_id: str) -> Dict[str, Any]:
    """计算从一个地图到另一个地图的移动消耗

    Returns:
        {"can_travel": bool, "reason": str,
         "stamina_cost": int, "time_desc": str}
    """
    from_map = MAPS.get(from_id)
    to_map = MAPS.get(to_id)

    if not from_map or not to_map:
        return {"can_travel": False, "reason": "地图不存在", "stamina_cost": 0, "time_desc": ""}

    # 必须相邻才能移动
    adj_ids = [a for a in from_map.get("adjacent", [])]
    if to_id not in adj_ids:
        return {"can_travel": False, "reason": "目的地与当前位置不相邻，无法直接前往",
                "stamina_cost": 0, "time_desc": ""}

    # 同世界层级内移动
    if from_map["world_tier"] == to_map["world_tier"]:
        stamina = 1
        time_desc = "约半日路程"
    else:
        # 跨世界层级移动（升界/降界），消耗更大
        tier_diff = abs(from_map["world_tier"] - to_map["world_tier"])
        stamina = 2 + tier_diff * 2
        time_desc = f"需跨越界限，约{tier_diff}日路程"

    return {
        "can_travel": True,
        "reason": "",
        "stamina_cost": stamina,
        "time_desc": time_desc,
        "to_name": to_map["name"],
        "to_desc": to_map.get("desc", ""),
    }


def check_travel_requirements(to_id: str, realm_id: int,
                               dao_heng: float = 0, dao_ni: float = 0,
                               dao_yan: float = 0) -> tuple:
    """检查玩家是否满足目标地图的进入条件

    Returns:
        (can_enter: bool, reason: str)
    """
    to_map = MAPS.get(to_id)
    if not to_map:
        return False, "目的地不存在"

    if realm_id < to_map["min_realm"]:
        from core.game.realms import format_realm_display
        return False, f"境界不足，需达到{format_realm_display(to_map['min_realm'])}"

    cond = to_map.get("unlock_condition")
    if cond:
        if realm_id < cond.get("min_realm", 0):
            from core.game.realms import format_realm_display
            return False, f"境界不足，需达到{format_realm_display(cond['min_realm'])}"
        if dao_ni < cond.get("dao_ni_pct", 0):
            return False, f"逆道亲和不足，需达到{cond['dao_ni_pct']}%"
        if dao_yan < cond.get("dao_yan_pct", 0):
            return False, f"衍道亲和不足，需达到{cond['dao_yan_pct']}%"
        if dao_heng < cond.get("dao_heng_pct", 0):
            return False, f"恒道亲和不足，需达到{cond['dao_heng_pct']}%"

    return True, ""


# 首次到达区域时的介绍文案
_FIRST_VISIT_TEXTS = {
    "canglan_city": "苍澜城，边陲小城，你修仙之路的起点。城中散修云集，坊市热闹，是新手历练的好去处。",
    "east_forest": "踏入东郊灵林，林中灵气比城内浓郁了些许。远处传来灵兽的低鸣，你握紧了手中的法器。",
    "south_market": "南市坊市人声鼎沸，各式灵材丹药法器琳琅满目。你第一次见到这么多修士聚集的地方。",
    "north_mountain": "北望灵山巍峨耸立，山顶云雾缭绕，灵气充沛。据说山中有前辈遗留的修炼洞府。",
    "fallen_star_lake": "落星湖畔，湖水清澈见底，据说此湖因一颗坠落的星辰而成。湖底偶尔闪烁着奇异的光芒。",
    "luoxia_valley": "落霞谷中灵气如雾，晚霞时分整个山谷都被染成金红色。这里是苍澜洲最好的修炼之地之一。",
    "canglan_mines": "苍澜矿脉深入地底，矿道中隐约可见灵矿的微光。这里产出的灵石虽品质一般，但对新手足够了。",
    "misty_swamp": "迷雾沼泽阴气弥漫，脚下的泥泞让你每一步都走得小心翼翼。传说沼泽深处有罕见的灵药。",
    "tianyuan_sect_city": "天元宗城巍峨壮观，比苍澜城大了数十倍。这里是天元大陆的修仙中心，各大宗门在此都有分堂。",
    "sword_peak": "万剑峰上剑气纵横，数百把无主飞剑在空中翱翔。天剑门的威压从山巅倾泻而下。",
    "pill_pavilion": "丹鼎阁周围弥漫着各种丹药的香气，有的清新提神，有的浓郁呛人。这里是天下丹师的圣地。",
}


def get_first_visit_text(map_id: str) -> Optional[str]:
    """获取首次到达某区域的介绍文案"""
    return _FIRST_VISIT_TEXTS.get(map_id)
