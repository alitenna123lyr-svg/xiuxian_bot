import asyncio
import time
from types import SimpleNamespace

import pytest

pytest.importorskip("telegram")

from adapters.telegram import bot as telegram_bot
from core.database import connection as db_conn


class _Msg:
    def __init__(self):
        self.chat = SimpleNamespace(id=12345, type="private")
        self.chat_id = 12345
        self.message_id = 10

    async def reply_text(self, text, **kwargs):
        return SimpleNamespace(chat_id=self.chat_id, message_id=self.message_id + 1)


class _Query:
    def __init__(self, data: str):
        self.id = "cb-admin-1"
        self.from_user = SimpleNamespace(id=7209751862)
        self.message = _Msg()
        self.data = data
        self.answered = []

    async def answer(self, text=None, show_alert=False):
        self.answered.append((text, bool(show_alert)))

    async def edit_message_text(self, text, **kwargs):
        return SimpleNamespace(chat_id=self.message.chat_id, message_id=self.message.message_id)


def test_admin_panel_callback_does_not_override_target_from_reply(monkeypatch):
    monkeypatch.setattr(telegram_bot, "_is_super_admin_tg", lambda _uid: True)

    async def _fake_fields():
        return [], {}

    captured = {}

    async def _fake_reply_with_owned_panel(update, context, text, **kwargs):
        captured["target"] = str(context.user_data.get("admin_target_token") or "")
        return None

    monkeypatch.setattr(telegram_bot, "_admin_modifiable_fields_snapshot", _fake_fields)
    monkeypatch.setattr(telegram_bot, "_reply_with_owned_panel", _fake_reply_with_owned_panel)

    message = _Msg()
    message.reply_to_message = SimpleNamespace(from_user=SimpleNamespace(id=8516652120, is_bot=False))
    update = SimpleNamespace(
        callback_query=SimpleNamespace(id="cb-1"),
        effective_message=message,
        effective_user=SimpleNamespace(id=7209751862),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(bot_data={}),
        user_data={"admin_target_token": "8248661472", "admin_target_uid": ""},
    )

    asyncio.run(telegram_bot._show_admin_test_panel(update, context))

    assert captured.get("target") == "8248661472"


def test_admin_resolve_target_user_prefers_tg_mapping(monkeypatch):
    monkeypatch.setattr(db_conn, "_pool", object())

    def _fake_get_user_by_id(uid):
        # 模拟存在一条历史脏数据：TG_ID 也被写成 user_id
        if uid == "7209751862":
            return {"user_id": "7209751862", "in_game_username": "dirty_row"}
        if uid == "1000014":
            return {"user_id": "1000014", "in_game_username": "real_user"}
        return None

    async def _fake_http_get(url, params=None, timeout=15):
        return {"success": True, "user_id": "1000014"}

    monkeypatch.setattr(db_conn, "get_user_by_id", _fake_get_user_by_id)
    monkeypatch.setattr(telegram_bot, "http_get", _fake_http_get)

    target_uid, target_user = asyncio.run(telegram_bot._admin_resolve_target_user("7209751862"))

    assert target_uid == "1000014"
    assert target_user and target_user.get("user_id") == "1000014"


def test_admin_quick_button_has_click_guard(monkeypatch):
    async def _fake_apply_preset(**kwargs):
        raise AssertionError("should not execute preset when click guard is active")

    monkeypatch.setattr(telegram_bot, "_is_super_admin_tg", lambda _uid: True)
    monkeypatch.setattr(telegram_bot, "_admin_apply_preset", _fake_apply_preset)
    context = SimpleNamespace(
        application=SimpleNamespace(bot_data={}),
        user_data={
            "admin_target_token": "1000014",
            "admin_quick_guard_key": "e1w:1000014",
            "admin_quick_guard_ts": int(time.time() * 1000) - 500,
        },
    )
    update = SimpleNamespace(callback_query=_Query("admin_test_quick_e1w"))

    asyncio.run(telegram_bot.callback_handler(update, context))

    assert any(item[0] == "操作已受理，请勿连点。" for item in update.callback_query.answered)
