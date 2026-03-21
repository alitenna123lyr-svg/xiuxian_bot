"""aiogram adapter entrypoint (full FSM coverage)."""

from __future__ import annotations

import asyncio
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from adapters.aiogram.legacy_bridge import close_legacy_bridge, router as legacy_router
from adapters.aiogram.services.api_client import close_http_session
from core.config import config
from core.utils.runtime_logging import setup_runtime_logging

logger = setup_runtime_logging("aiogram", project_root=ROOT_DIR, stats_interval_seconds=120)


def _telegram_token() -> str:
    token_source = config.telegram_token
    if callable(token_source):
        return str(token_source() or "").strip()
    return str(token_source or "").strip()


async def main() -> None:
    token = _telegram_token()
    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN/XXBOT_TELEGRAM_TOKEN")

    bot = Bot(token=token)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(legacy_router)

    logger.info("aiogram adapter starting (full_fsm_coverage)")
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await close_legacy_bridge()
        await close_http_session()
        await bot.session.close()
        logger.info("aiogram adapter stopped")


if __name__ == "__main__":
    asyncio.run(main())
