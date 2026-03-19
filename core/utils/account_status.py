"""
用户状态工具
"""

import logging
from core.database.connection import fetch_one, refresh_user_stamina, refresh_user_vitals, DEFAULT_STAMINA_MAX
from core.game.realms import get_realm_by_id, get_next_realm, format_realm_progress
from core.game.currency import wallet_from_user
from core.services.sect_service import apply_sect_stat_buffs, get_user_sect_buffs

logger = logging.getLogger(__name__)


def _format_stamina_value(value):
    try:
        val = float(value)
    except (TypeError, ValueError):
        return value
    if abs(val - int(val)) < 1e-6:
        return int(val)
    return round(val, 1)


def get_user_status(user_id):
    """获取用户完整状态"""
    try:
        refresh_user_stamina(user_id)
        refresh_user_vitals(user_id)
        user = fetch_one("SELECT * FROM users WHERE user_id = %s", (user_id,))
        
        if not user:
            return None
        user = apply_sect_stat_buffs(user)
        sect_buffs = user.get("sect_buffs") or get_user_sect_buffs(user_id)
        wallet = wallet_from_user(user)

        rank = user.get('rank', 1)
        realm = get_realm_by_id(rank)
        next_realm = get_next_realm(rank)
        
        element = user.get("element") or "无"
        
        current_exp = user.get('exp', 0)
        next_exp = next_realm['exp_required'] if next_realm else None
        
        return {
            'user_id': user_id,
            'in_game_username': user.get('in_game_username', '未知'),
            'rank': rank,
            'realm_name': realm['name'] if realm else "未知",
            'exp': current_exp,
            'next_exp': next_exp,
            'element': element,
            'copper': user.get('copper', 0),
            'gold': user.get('gold', 0),
            'spirit_stone_low': wallet.get('spirit_low', 0),
            'spirit_stone_mid': wallet.get('spirit_mid', 0),
            'spirit_stone_high': wallet.get('spirit_high', 0),
            'spirit_stone_exquisite': wallet.get('spirit_exquisite', 0),
            'spirit_stone_supreme': wallet.get('spirit_supreme', 0),
            'immortal_stone_flawed': wallet.get('immortal_flawed', 0),
            'immortal_stone_low': wallet.get('immortal_low', 0),
            'immortal_stone_mid': wallet.get('immortal_mid', 0),
            'immortal_stone_high': wallet.get('immortal_high', 0),
            'immortal_stone_supreme': wallet.get('immortal_supreme', 0),
            'stamina': user.get('stamina', DEFAULT_STAMINA_MAX),
            'max_stamina': DEFAULT_STAMINA_MAX,
            'hp': user.get('hp', 100),
            'mp': user.get('mp', 50),
            'max_hp': user.get('max_hp', 100),
            'max_mp': user.get('max_mp', 50),
            'attack': user.get('attack', 10),
            'defense': user.get('defense', 5),
            'crit_rate': user.get('crit_rate', 0.05),
            'dy_times': user.get('dy_times', 0),
            'breakthrough_pity': user.get('breakthrough_pity', 0),
            'state': user.get('state', False),
            'lang': user.get('lang', 'CHS'),
            'equipped_weapon': user.get('equipped_weapon'),
            'equipped_armor': user.get('equipped_armor'),
            'equipped_accessory1': user.get('equipped_accessory1'),
            'equipped_accessory2': user.get('equipped_accessory2'),
            'sect_buffs': sect_buffs,
        }
        
    except Exception:
        logger.exception("Error getting user status for %s", user_id)
        return None


def format_status_text(status_info, lang="CHS", platform=None, equipped_items=None):
    """格式化状态显示"""
    if not status_info:
        return "❌ 用户信息未找到"

    # 进度条
    next_exp = status_info.get('next_exp')
    current_exp = status_info.get('exp', 0)

    if next_exp:
        progress = min(100, int(current_exp / next_exp * 100))
        bar_length = 15
        filled = int(bar_length * progress / 100)
        progress_bar = '█' * filled + '░' * (bar_length - filled)
        exp_text = f"{progress_bar} {progress}%\n├ 修为: {current_exp:,} / {next_exp:,}"
    else:
        exp_text = f"├ 修为: {current_exp:,} (已满级)"

    # 状态
    state_text = "🧘 修炼中" if status_info.get("state") else "💤 空闲"

    # 装备信息
    equip_lines = ""
    if equipped_items:
        equip_parts = []
        for slot, item in equipped_items.items():
            if item:
                equip_parts.append(f"  {item}")
        if equip_parts:
            equip_lines = "\n".join(equip_parts)

    text = f"""
╔══════════════════════╗
║  *{status_info.get('in_game_username', '未知')}*
╠══════════════════════╣
├ 🔮 境界: {status_info.get('realm_name', '凡人')} (Lv.{status_info.get('rank', 1)})
├ 🌟 五行: {status_info.get('element', '无')}
├ 💰 下品灵石: {status_info.get('copper', 0):,}
├ 💎 中品灵石: {status_info.get('gold', 0):,}
├ ⚡ 精力: {_format_stamina_value(status_info.get('stamina', DEFAULT_STAMINA_MAX))} / {status_info.get('max_stamina', DEFAULT_STAMINA_MAX)}
╠══════════════════════╣
├ ❤️ HP: {status_info.get('hp', 100)} / {status_info.get('max_hp', 100)}
├ 💙 MP: {status_info.get('mp', 50)} / {status_info.get('max_mp', 50)}
├ ⚔️ 攻击: {status_info.get('attack', 10)}
├ 🛡️ 防御: {status_info.get('defense', 5)}
╠══════════════════════╣
{exp_text}
├ 🎯 狩猎次数: {status_info.get('dy_times', 0)}
├ 📍 状态: {state_text}"""

    if equip_lines:
        text += f"""
╠══════════════════════╣
├ 👕 装备:
{equip_lines}"""
    sect_buffs = status_info.get("sect_buffs") or {}
    if sect_buffs.get("in_sect"):
        text += (
            f"\n╠══════════════════════╣\n"
            f"├ 🏛️ 宗门: {sect_buffs.get('sect_name')}\n"
            f"├ 修炼加成: +{int(float(sect_buffs.get('cultivation_pct', 0) or 0))}%\n"
            f"├ 属性加成: +{int(float(sect_buffs.get('stat_pct', 0) or 0))}%\n"
            f"├ 战斗收益: +{int(float(sect_buffs.get('battle_reward_pct', 0) or 0))}%"
        )

    text += "\n╚══════════════════════╝\n"
    return text


def check_user_exists(user_id):
    """检查用户是否存在"""
    try:
        user = fetch_one("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        return user is not None
    except Exception:
        logger.exception("Error checking user existence for %s", user_id)
        return False
