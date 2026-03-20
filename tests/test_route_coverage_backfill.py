from flask import Flask

from core.routes.combat import list_monsters, list_realms, secret_realms_explore
from core.routes.cultivation import (
    cultivate_start,
    cultivate_status,
    cultivate_end,
    realm_trial_status,
    signin_status,
)
from core.routes.equipment import (
    enhance_item,
    forge_status,
    forge_post,
    forge_catalog_get,
    forge_targeted_post,
    unequip_item,
)
from core.routes.events import events_list, events_status, events_exchange
from core.routes.gacha import gacha_pity
from core.routes.health import api_health_check
from core.routes.pvp import pvp_ranking, pvp_records
from core.routes.quests import quest_claim_all
from core.routes.sect import sect_buffs, sect_quests, sect_quests_claim, sect_transfer
from core.routes.skills import skill_equip, skill_unequip, skill_upgrade
from core.routes.social import social_chat_reject
from core.routes.user import codex_get
from tests.conftest import create_user


def _unwrap_route_result(resp):
    if isinstance(resp, tuple):
        response_obj, status_code = resp
        return int(status_code), response_obj.get_json() or {}
    return int(resp.status_code), resp.get_json() or {}


def test_catalog_and_health_routes_cover_uncovered_endpoints(test_db):
    app = Flask(__name__)

    with app.test_request_context("/api/health", method="GET"):
        status, payload = _unwrap_route_result(api_health_check())
    assert status == 200
    assert payload.get("success") is True

    with app.test_request_context("/api/realms", method="GET"):
        status, payload = _unwrap_route_result(list_realms())
    assert status == 200
    assert payload.get("success") is True
    assert payload.get("realms")

    with app.test_request_context("/api/monsters", method="GET"):
        status, payload = _unwrap_route_result(list_monsters())
    assert status == 200
    assert payload.get("success") is True
    assert isinstance(payload.get("monsters"), list)


def test_codex_get_supports_items_and_monsters(test_db):
    create_user("u1", "甲", rank=5)
    app = Flask(__name__)

    with app.test_request_context(
        "/api/codex/u1%skind=items",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        status_items, payload_items = _unwrap_route_result(codex_get("u1"))
    assert status_items == 200
    assert payload_items.get("kind") == "items"
    assert "items" in payload_items

    with app.test_request_context(
        "/api/codex/u1%skind=monsters",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        status_mons, payload_mons = _unwrap_route_result(codex_get("u1"))
    assert status_mons == 200
    assert payload_mons.get("kind") == "monsters"
    assert "monsters" in payload_mons


def test_cultivation_status_trial_and_signin_routes(test_db):
    create_user("u1", "甲", rank=5)
    app = Flask(__name__)

    with app.test_request_context(
        "/api/cultivate/start",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        start_status, _ = _unwrap_route_result(cultivate_start())
    assert start_status == 200

    with app.test_request_context(
        "/api/cultivate/status/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        status_status, status_payload = _unwrap_route_result(cultivate_status("u1"))
    assert status_status == 200
    assert status_payload.get("success") is True

    with app.test_request_context(
        "/api/cultivate/end",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        end_status, end_payload = _unwrap_route_result(cultivate_end())
    assert end_status == 200
    assert end_payload.get("success") is True

    with app.test_request_context(
        "/api/realm-trial/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        trial_status, trial_payload = _unwrap_route_result(realm_trial_status("u1"))
    assert trial_status == 200
    assert trial_payload.get("success") is True
    assert "trial" in trial_payload

    with app.test_request_context(
        "/api/signin/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        signin_stat, signin_payload = _unwrap_route_result(signin_status("u1"))
    assert signin_stat == 200
    assert signin_payload.get("success") is True
    assert "signed_today" in signin_payload


def test_equipment_uncovered_routes(test_db, monkeypatch):
    create_user("u1", "甲", rank=8)
    app = Flask(__name__)

    with app.test_request_context(
        "/api/enhance",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        enhance_status, enhance_payload = _unwrap_route_result(enhance_item())
    assert enhance_status == 400
    assert enhance_payload.get("code") == "MISSING_PARAMS"

    with app.test_request_context(
        "/api/unequip",
        method="POST",
        json={"user_id": "u1", "slot": "bad_slot"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        unequip_status, unequip_payload = _unwrap_route_result(unequip_item())
    assert unequip_status == 400
    assert unequip_payload.get("success") is False

    with app.test_request_context(
        "/api/forge/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        forge_status_code, forge_status_payload = _unwrap_route_result(forge_status("u1"))
    assert forge_status_code == 200
    assert forge_status_payload.get("success") is True

    with app.test_request_context(
        "/api/forge/catalog/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        catalog_status, catalog_payload = _unwrap_route_result(forge_catalog_get("u1"))
    assert catalog_status == 200
    assert catalog_payload.get("success") is True
    assert "items" in catalog_payload

    monkeypatch.setattr(
        "core.routes.equipment.do_forge",
        lambda user_id, cfg, mode="normal": ({"success": True, "user_id": user_id, "mode": mode}, 200),
    )
    with app.test_request_context(
        "/api/forge",
        method="POST",
        json={"user_id": "u1", "mode": "normal"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        forge_post_status, forge_post_payload = _unwrap_route_result(forge_post())
    assert forge_post_status == 200
    assert forge_post_payload.get("success") is True

    monkeypatch.setattr(
        "core.routes.equipment.forge_targeted",
        lambda user_id, item_id, cfg: ({"success": True, "user_id": user_id, "item_id": item_id}, 200),
    )
    with app.test_request_context(
        "/api/forge/targeted",
        method="POST",
        json={"user_id": "u1", "item_id": "iron_ore"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        targeted_status, targeted_payload = _unwrap_route_result(forge_targeted_post())
    assert targeted_status == 200
    assert targeted_payload.get("success") is True


def test_events_uncovered_routes(test_db):
    create_user("u1", "甲", rank=6)
    app = Flask(__name__)

    with app.test_request_context("/api/events", method="GET"):
        events_status_code, events_payload = _unwrap_route_result(events_list())
    assert events_status_code == 200
    assert events_payload.get("success") is True
    assert isinstance(events_payload.get("events"), list)

    with app.test_request_context(
        "/api/events/status/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        status_code, status_payload = _unwrap_route_result(events_status("u1"))
    assert status_code == 200
    assert status_payload.get("success") is True

    with app.test_request_context(
        "/api/events/exchange",
        method="POST",
        json={"user_id": "u1", "event_id": "spring_festival"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        exchange_status, exchange_payload = _unwrap_route_result(events_exchange())
    assert exchange_status == 400
    assert exchange_payload.get("code") == "MISSING_PARAMS"


def test_events_exchange_invalid_quantity_returns_400(test_db):
    create_user("u1", "甲", rank=6)
    app = Flask(__name__)
    with app.test_request_context(
        "/api/events/exchange",
        method="POST",
        json={
            "user_id": "u1",
            "event_id": "spring_festival",
            "exchange_id": "sf_spirit_stone",
            "quantity": "abc",
        },
        headers={"X-Actor-User-Id": "u1"},
    ):
        status_code, payload = _unwrap_route_result(events_exchange())
    assert status_code == 400
    assert payload.get("code") == "INVALID_PARAMS"


def test_gacha_pity_route_validation(test_db):
    create_user("u1", "甲", rank=6)
    app = Flask(__name__)
    with app.test_request_context(
        "/api/gacha/pity/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(gacha_pity("u1"))
    assert status == 400
    assert payload.get("code") == "MISSING_PARAMS"


def test_pvp_ranking_and_records_routes(test_db):
    create_user("u1", "甲", rank=6)
    app = Flask(__name__)

    with app.test_request_context("/api/pvp/ranking", method="GET"):
        ranking_status, ranking_payload = _unwrap_route_result(pvp_ranking())
    assert ranking_status == 200
    assert ranking_payload.get("success") is True
    assert "entries" in ranking_payload

    with app.test_request_context(
        "/api/pvp/records/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        records_status, records_payload = _unwrap_route_result(pvp_records("u1"))
    assert records_status == 200
    assert records_payload.get("success") is True
    assert isinstance(records_payload.get("records"), list)


def test_quest_claim_all_route(test_db):
    create_user("u1", "甲", rank=5)
    app = Flask(__name__)
    with app.test_request_context(
        "/api/quests/claim_all",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(quest_claim_all())
    assert status == 200
    assert payload.get("success") is True
    assert payload.get("claimed_count") == 0


def test_sect_uncovered_routes(test_db, monkeypatch):
    create_user("u1", "甲", rank=8)
    app = Flask(__name__)

    with app.test_request_context(
        "/api/sect/buffs/u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        buffs_status, buffs_payload = _unwrap_route_result(sect_buffs("u1"))
    assert buffs_status == 200
    assert buffs_payload.get("success") is True
    assert "buffs" in buffs_payload

    monkeypatch.setattr(
        "core.routes.sect.get_quests",
        lambda sect_id, user_id=None: ({"success": True, "quests": [], "sect_id": sect_id}, 200),
    )
    with app.test_request_context(
        "/api/sect/quests/S1%suser_id=u1",
        method="GET",
        headers={"X-Actor-User-Id": "u1"},
    ):
        quests_status, quests_payload = _unwrap_route_result(sect_quests("S1"))
    assert quests_status == 200
    assert quests_payload.get("success") is True

    monkeypatch.setattr(
        "core.routes.sect.claim_quest",
        lambda user_id, quest_id: ({"success": True, "user_id": user_id, "quest_id": quest_id}, 200),
    )
    with app.test_request_context(
        "/api/sect/quests/claim",
        method="POST",
        json={"user_id": "u1", "quest_id": 1},
        headers={"X-Actor-User-Id": "u1"},
    ):
        claim_status, claim_payload = _unwrap_route_result(sect_quests_claim())
    assert claim_status == 200
    assert claim_payload.get("success") is True

    monkeypatch.setattr(
        "core.routes.sect.transfer_leadership",
        lambda user_id, target_user_id: ({"success": True, "user_id": user_id, "target_user_id": target_user_id}, 200),
    )
    with app.test_request_context(
        "/api/sect/transfer",
        method="POST",
        json={"user_id": "u1", "target_user_id": "u2"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        transfer_status, transfer_payload = _unwrap_route_result(sect_transfer())
    assert transfer_status == 200
    assert transfer_payload.get("success") is True


def test_skills_uncovered_routes(test_db):
    create_user("u1", "甲", rank=8)
    app = Flask(__name__)

    with app.test_request_context(
        "/api/skills/equip",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        equip_status, equip_payload = _unwrap_route_result(skill_equip())
    assert equip_status == 400
    assert equip_payload.get("success") is False

    with app.test_request_context(
        "/api/skills/unequip",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        unequip_status, unequip_payload = _unwrap_route_result(skill_unequip())
    assert unequip_status == 200
    assert unequip_payload.get("success") is True

    with app.test_request_context(
        "/api/skills/upgrade",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        upgrade_status, upgrade_payload = _unwrap_route_result(skill_upgrade())
    assert upgrade_status == 400
    assert upgrade_payload.get("success") is False


def test_social_reject_route_validation(test_db):
    create_user("u1", "甲", rank=5)
    app = Flask(__name__)
    with app.test_request_context(
        "/api/social/chat/reject",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(social_chat_reject())
    assert status == 400
    assert payload.get("code") == "MISSING_PARAMS"


def test_secret_realm_explore_validation_route(test_db):
    create_user("u1", "甲", rank=8)
    app = Flask(__name__)
    with app.test_request_context(
        "/api/secret-realms/explore",
        method="POST",
        json={"user_id": "u1"},
        headers={"X-Actor-User-Id": "u1"},
    ):
        status, payload = _unwrap_route_result(secret_realms_explore())
    assert status == 400
    assert payload.get("code") == "MISSING_PARAMS"
