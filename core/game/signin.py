"""
每日签到系统 - Daily Sign-in System
"""

import time
import datetime
from typing import Dict, Any, Optional, Tuple
import random

from core.utils.timeutil import midnight_timestamp
from core.config import config
from core.utils.reward_scaling import rank_scale


# 签到奖励配置
SIGNIN_REWARDS = {
    1: {"copper": 120, "exp": 50, "gold": 0, "item": {"id": "herb", "quantity": 2}},
    2: {"copper": 180, "exp": 80, "gold": 0, "item": {"id": "iron_ore", "quantity": 3}},
    3: {"copper": 220, "exp": 120, "gold": 0, "item": {"id": "small_exp_pill", "quantity": 1}},
    4: {"copper": 260, "exp": 150, "gold": 1, "item": {"id": "spirit_stone", "quantity": 2}},
    5: {"copper": 320, "exp": 200, "gold": 1, "item": {"id": "breakthrough_pill", "quantity": 1}},
    6: {"copper": 420, "exp": 300, "gold": 2, "item": {"id": "spirit_herb", "quantity": 2}},
    7: {"copper": 520, "exp": 500, "gold": 5, "item": {"id": "demon_core", "quantity": 1}},
}

DEFAULT_MONTH_MILESTONES = {
    7: {"copper": 300, "exp": 120, "gold": 1, "item": {"id": "herb", "quantity": 3}},
    14: {"copper": 500, "exp": 240, "gold": 1, "item": {"id": "spirit_stone", "quantity": 2}},
    21: {"copper": 800, "exp": 360, "gold": 2, "item": {"id": "breakthrough_pill", "quantity": 1}},
    28: {"copper": 1200, "exp": 520, "gold": 3, "item": {"id": "demon_core", "quantity": 1}},
}


def _item_display(item: Optional[Dict[str, Any]]) -> str:
    if not item:
        return ""
    try:
        from core.game.items import get_item_by_id
        item_def = get_item_by_id(item["id"])
        item_name = item_def["name"] if item_def else item["id"]
    except Exception:
        item_name = item["id"]
    return f"{item_name} x{item['quantity']}"


def _reward_lines(reward: Dict[str, Any]) -> list[str]:
    lines = [
        f"• 下品灵石: {reward['copper']}",
        f"• 修为: {reward['exp']}",
    ]
    if reward.get("gold", 0) > 0:
        lines.append(f"• 中品灵石: {reward['gold']}")
    if reward.get("item"):
        lines.append(f"• 物品: {_item_display(reward['item'])}")
    return lines


def get_signin_tomorrow_hint(consecutive_days: int, user_rank: int = 1) -> str:
    next_reward = get_signin_reward(consecutive_days + 1, user_rank)
    next_day = next_reward["day"]
    highlights = []
    if next_reward.get("gold", 0) > 0:
        highlights.append(f"{next_reward['gold']} 中品灵石")
    if next_reward.get("item"):
        highlights.append(_item_display(next_reward["item"]))
    if next_day == 7:
        highlights.append("7 日满签大奖")
    if not highlights:
        highlights.append(f"{next_reward['exp']} 修为 + {next_reward['copper']} 下品灵石")
    return f"⏰ 明天最值得回来拿：第 {next_day} 天的 {'、'.join(highlights)}"


def get_today_timestamp() -> int:
    """获取今天0点的时间戳（北京时间）"""
    return midnight_timestamp()


def check_signed_today(sign_timestamp: Optional[int]) -> bool:
    """检查今天是否已签到"""
    if sign_timestamp is None:
        return False
    today_start = get_today_timestamp()
    return sign_timestamp >= today_start


def get_consecutive_days(last_sign: Optional[int], current_streak: int) -> int:
    """
    计算连续签到天数
    - 如果昨天签到了，连续天数+1
    - 如果中断了，重置为1
    """
    if last_sign is None:
        return 1
    
    today_start = get_today_timestamp()
    yesterday_start = today_start - 86400
    
    if last_sign >= yesterday_start:
        # 昨天或今天签到了
        if last_sign >= today_start:
            # 今天已签到，返回当前连续天数
            return current_streak
        else:
            # 昨天签到，今天还没，连续+1
            return current_streak + 1
    else:
        # 中断了
        return 1


def get_signin_reward(consecutive_days: int, user_rank: int = 1) -> Dict[str, Any]:
    """
    获取签到奖励
    - 连续签到7天后重置
    - 第7天奖励最丰厚
    - 奖励按玩家境界缩放
    """
    # 7天一个周期
    day_in_cycle = ((consecutive_days - 1) % 7) + 1
    reward = SIGNIN_REWARDS.get(day_in_cycle, SIGNIN_REWARDS[1]).copy()

    # 按境界分段缩放（中品灵石不缩放，保持稀缺性）
    rank_mult = rank_scale(int(user_rank or 1))
    reward["copper"] = int(reward["copper"] * rank_mult)
    reward["exp"] = int(reward["exp"] * rank_mult)

    reward["day"] = day_in_cycle
    reward["consecutive_days"] = consecutive_days
    return reward


def format_signin_status(user_data: Dict) -> str:
    """格式化签到状态"""
    sign = user_data.get("sign", 0)
    last_sign = user_data.get("last_sign_timestamp")
    consecutive = user_data.get("consecutive_sign_days", 0)
    user_rank = user_data.get("rank", 1)
    
    today_start = get_today_timestamp()
    signed_today = last_sign and last_sign >= today_start
    month_key = user_data.get("signin_month_key") or ""
    month_days = int(user_data.get("signin_month_days", 0) or 0)
    
    if signed_today:
        # 已签到
        today_reward = get_signin_reward(consecutive, user_rank)
        next_reward = get_signin_reward(consecutive + 1, user_rank)
        today_lines = "\n".join(_reward_lines(today_reward))
        next_lines = "\n".join(_reward_lines(next_reward))
        tomorrow_hint = get_signin_tomorrow_hint(consecutive, user_rank)
        month_line = f"\n📅 本月已签到: {month_days} 天" if month_key else ""
        text = f"""
📅 *每日签到*

✅ 今日已签到

📊 连续签到: {consecutive} 天
🎯 当前周期: 第 {((consecutive - 1) % 7) + 1} 天
{month_line}

今日签到奖励:
{today_lines}

明天签到奖励:
{next_lines}

{tomorrow_hint}
"""
    else:
        # 未签到
        current_streak = get_consecutive_days(last_sign, consecutive)
        reward = get_signin_reward(current_streak, user_rank)
        reward_lines = "\n".join(_reward_lines(reward))
        tomorrow_hint = get_signin_tomorrow_hint(current_streak, user_rank)
        
        month_line = f"\n📅 本月已签到: {month_days} 天" if month_key else ""
        text = f"""
📅 *每日签到*

❌ 今日未签到

📊 连续签到: {consecutive} 天
🎯 本次签到: 第 {current_streak} 天
{month_line}

签到奖励预览:
{reward_lines}

{tomorrow_hint}
"""
    
    return text


def do_signin(user_data: Dict) -> Tuple[bool, Dict[str, Any], str]:
    """
    执行签到
    返回: (是否成功, 奖励数据, 消息)
    """
    last_sign = user_data.get("last_sign_timestamp")
    consecutive = user_data.get("consecutive_sign_days", 0)
    
    # 检查是否已签到
    if check_signed_today(last_sign):
        user_rank = user_data.get("rank", 1)
        reward = get_signin_reward(consecutive, user_rank)
        item_text = ""
        if reward.get("item"):
            item_text = f"\n🎁 物品: {reward['item']['id']} x{reward['item']['quantity']}"
        message = f"""
✅ 今日已签到

📊 连续签到: {consecutive} 天
🎯 当前周期: 第 {reward['day']} 天

🎁 *今日奖励:*
• 下品灵石: +{reward['copper']}
• 修为: +{reward['exp']}
{f"• 中品灵石: +{reward['gold']}" if reward.get('gold', 0) > 0 else ""}{item_text}
"""
        return False, {"rewards": reward}, message.strip()

    def _month_key(ts: int) -> str:
        tz = datetime.timezone(datetime.timedelta(hours=8))
        return datetime.datetime.fromtimestamp(ts, tz=tz).strftime("%Y-%m")

    def _month_milestones() -> Dict[int, Dict[str, Any]]:
        cfg = config.get_nested("balance", "signin_month_milestones", default=None)
        if isinstance(cfg, list) and cfg:
            result: Dict[int, Dict[str, Any]] = {}
            for entry in cfg:
                try:
                    day = int(entry.get("day", 0) or 0)
                except (TypeError, ValueError):
                    continue
                if day <= 0:
                    continue
                result[day] = {
                    "copper": int(entry.get("copper", 0) or 0),
                    "exp": int(entry.get("exp", 0) or 0),
                    "gold": int(entry.get("gold", 0) or 0),
                    "item": entry.get("item"),
                }
            if result:
                return result
        return DEFAULT_MONTH_MILESTONES.copy()
    
    # 计算连续天数
    new_consecutive = get_consecutive_days(last_sign, consecutive)
    now_ts = int(time.time())

    # 月度累计签到
    month_key = _month_key(now_ts)
    prev_month_key = str(user_data.get("signin_month_key") or "")
    month_days = int(user_data.get("signin_month_days", 0) or 0)
    month_bits = int(user_data.get("signin_month_claim_bits", 0) or 0)
    if prev_month_key != month_key:
        month_days = 0
        month_bits = 0
    month_days += 1
    milestone_cfg = _month_milestones()
    milestone_days = sorted(milestone_cfg.keys())
    month_bonus: Optional[Dict[str, Any]] = None
    if month_days in milestone_cfg:
        try:
            bit = 1 << milestone_days.index(month_days)
        except ValueError:
            bit = 0
        if bit and (month_bits & bit) == 0:
            month_bits |= bit
            month_bonus = milestone_cfg.get(month_days)

    # 获取奖励（按境界缩放）
    user_rank = user_data.get("rank", 1)
    reward = get_signin_reward(new_consecutive, user_rank)
    
    # 返回更新数据和奖励
    updates = {
        "sign": 1,
        "last_sign_timestamp": now_ts,
        "consecutive_sign_days": new_consecutive,
        "max_signin_days": max(
            int(user_data.get("max_signin_days", 0) or 0),
            int(consecutive or 0),
            int(new_consecutive or 0),
        ),
        "signin_month_key": month_key,
        "signin_month_days": month_days,
        "signin_month_claim_bits": month_bits,
    }
    
    # 添加奖励到返回数据
    rewards = {
        "copper": reward["copper"],
        "exp": reward["exp"],
        "gold": reward.get("gold", 0),
        "item": reward.get("item"),
        "consecutive_days": new_consecutive,
        "day_in_cycle": reward["day"],
    }
    if month_bonus:
        rewards["month_bonus"] = month_bonus
        rewards["month_days"] = month_days
    
    reward_lines = [f"• 下品灵石: +{reward['copper']}", f"• 修为: +{reward['exp']}"]
    if reward.get('gold', 0) > 0:
        reward_lines.append(f"• 中品灵石: +{reward['gold']}")
    if reward.get("item"):
        reward_lines.append(f"• 物品: {_item_display(reward['item'])}")
    tomorrow_hint = get_signin_tomorrow_hint(new_consecutive, user_rank)
    reward_text = "\n".join(reward_lines)
    
    message = f"""
✅ *签到成功！*

📅 连续签到: {new_consecutive} 天
🎯 当前周期: 第 {reward['day']} 天

🎁 *获得奖励:*
{reward_text}

{'🎉 连续签到7天完成！周期重置！' if reward['day'] == 7 else '继续加油！'}
{tomorrow_hint}
"""
    
    return True, {"updates": updates, "rewards": rewards}, message
