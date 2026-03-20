# Smoke Scripts

**Recommended**
- `smoke_bot_layer.py`: Bot-level integration smoke (simulates Telegram updates, no network).
- `smoke_api_e2e.py`: Core API smoke via Flask test client (no network).
- `smoke_social_chat.py`: 论道精力规则专项验证。

**Database**
- 冒烟脚本默认连接当前 PostgreSQL 配置（`DATABASE_URL` 或 `POSTGRES_*`）。
- 运行前请确认目标库可写（脚本会创建/更新测试数据）。

**Quick Regression**
- `pytest -m smoke -q`
- `python scripts/smoke_bot_layer.py`
