"""Resource conversion configuration helpers."""

from __future__ import annotations

from typing import Dict, Any, List

from core.config import config


DEFAULT_ROUTES: Dict[str, Dict[str, Any]] = {
    "steady": {
        "name": "稳妥转化",
        "desc": "高损耗但稳定，适合稳健囤资源。",
        "cost_mult": 1.10,
        "output_mult": 1.00,
        "success_rate": 1.0,
        "fail_output_mult": 1.0,
        "requires_catalyst": False,
    },
    "risky": {
        "name": "投机转化",
        "desc": "低成本高波动，可能爆发或大亏。",
        "cost_mult": 0.95,
        "output_mult": 1.60,
        "success_rate": 0.45,
        "fail_output_mult": 0.40,
        "requires_catalyst": False,
    },
    "focused": {
        "name": "专精转化",
        "desc": "消耗额外材料换更高效率，适合定向培养。",
        "cost_mult": 1.05,
        "output_mult": 1.25,
        "success_rate": 1.0,
        "fail_output_mult": 1.0,
        "requires_catalyst": True,
    },
}


DEFAULT_TARGETS: List[Dict[str, Any]] = [
    {"item_id": "iron_ore", "min_rank": 1, "base_copper": 12},
    {"item_id": "herb", "min_rank": 1, "base_copper": 24},
    {"item_id": "spirit_stone", "min_rank": 5, "base_copper": 60},
    {"item_id": "spirit_herb", "min_rank": 8, "base_copper": 120},
    {"item_id": "demon_core", "min_rank": 10, "base_copper": 360},
    {"item_id": "recipe_fragment", "min_rank": 10, "base_copper": 216},
    {"item_id": "dragon_scale", "min_rank": 20, "base_copper": 600},
    {"item_id": "phoenix_feather", "min_rank": 20, "base_copper": 600},
]


DEFAULT_FOCUSED_CATALYST: Dict[str, str] = {
    "iron_ore": "iron_ore",
    "herb": "herb",
    "spirit_stone": "iron_ore",
    "spirit_herb": "herb",
    "demon_core": "spirit_stone",
    "recipe_fragment": "spirit_herb",
    "dragon_scale": "recipe_fragment",
    "phoenix_feather": "recipe_fragment",
}


def _clone_list(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [dict(row) for row in items]


def _clone_dict(items: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {k: dict(v) for k, v in items.items()}


def _validate_route(route_name: str, row: Dict[str, Any]) -> Dict[str, Any]:
    cfg = dict(row or {})
    cost_mult = float(cfg.get("cost_mult", 1.0) or 0.0)
    success_rate = float(cfg.get("success_rate", 1.0) or 0.0)
    fail_output_mult = float(cfg.get("fail_output_mult", 1.0) or 0.0)
    if cost_mult <= 0:
        raise ValueError(f"resource_conversion.routes.{route_name}.cost_mult 必须大于 0")
    if success_rate < 0 or success_rate > 1:
        raise ValueError(f"resource_conversion.routes.{route_name}.success_rate 必须在 [0,1] 范围内")
    if fail_output_mult < 0:
        raise ValueError(f"resource_conversion.routes.{route_name}.fail_output_mult 不能小于 0")
    cfg["cost_mult"] = cost_mult
    cfg["success_rate"] = success_rate
    cfg["fail_output_mult"] = fail_output_mult
    cfg["output_mult"] = float(cfg.get("output_mult", 1.0) or 1.0)
    cfg["requires_catalyst"] = bool(cfg.get("requires_catalyst", False))
    return cfg


def _validate_target(row: Dict[str, Any]) -> Dict[str, Any]:
    target = dict(row or {})
    item_id = str(target.get("item_id") or "").strip()
    if not item_id:
        raise ValueError("resource_conversion.targets[].item_id 不能为空")
    min_rank = int(target.get("min_rank", 1) or 1)
    base_copper = int(target.get("base_copper", 0) or 0)
    if min_rank < 1:
        raise ValueError(f"resource_conversion.targets[{item_id}].min_rank 必须大于等于 1")
    if base_copper <= 0:
        raise ValueError(f"resource_conversion.targets[{item_id}].base_copper 必须大于 0")
    target["item_id"] = item_id
    target["min_rank"] = min_rank
    target["base_copper"] = base_copper
    return target


def get_resource_conversion_config() -> Dict[str, Any]:
    cfg = config.get_nested("balance", "resource_conversion", default={}) or {}
    routes = cfg.get("routes") or DEFAULT_ROUTES
    targets = cfg.get("targets") or DEFAULT_TARGETS
    catalysts = cfg.get("focused_catalyst") or DEFAULT_FOCUSED_CATALYST
    disabled = set(cfg.get("disabled_targets") or [])
    if disabled:
        targets = [row for row in targets if row.get("item_id") not in disabled]
    max_batch = int(cfg.get("max_batch", 20))
    if max_batch < 1:
        raise ValueError("resource_conversion.max_batch 必须大于等于 1")
    catalyst_per_batch = int(cfg.get("focused_catalyst_per_batch", 1))
    if catalyst_per_batch < 1:
        raise ValueError("resource_conversion.focused_catalyst_per_batch 必须大于等于 1")
    normalized_routes = {str(k): _validate_route(str(k), v) for k, v in _clone_dict(routes).items()}
    normalized_targets = [_validate_target(row) for row in _clone_list(targets)]
    return {
        "routes": normalized_routes,
        "targets": normalized_targets,
        "focused_catalyst": dict(catalysts),
        "max_batch": max_batch,
        "focused_catalyst_per_batch": catalyst_per_batch,
    }


def resolve_target_config(targets: List[Dict[str, Any]], item_id: str) -> Dict[str, Any] | None:
    for row in targets:
        if row.get("item_id") == item_id:
            return dict(row)
    return None
