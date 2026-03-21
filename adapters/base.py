"""适配器抽象基类。

所有平台适配器继承此类，获得统一的 HTTP 客户端、日志、语言管理等能力。
"""

import os
import sys
import logging
import json
from abc import ABC, abstractmethod
from typing import Any, Dict

import aiohttp

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.config import config
from adapters.actor_paths import compiled_actor_path_patterns


_ACTOR_PATH_PATTERNS = compiled_actor_path_patterns()


class BaseAdapter(ABC):
    """平台适配器抽象基类。"""

    PLATFORM: str = ""
    ADAPTER_VERSION: str = ""

    def __init__(self):
        self.server_url = str(getattr(config, "core_server_url", "") or f"http://127.0.0.1:{config.core_server_port}").rstrip("/")
        self.internal_api_token = (config.internal_api_token or "").strip()
        self.logger = self._setup_logger()

    # ---- 日志 ----

    def _setup_logger(self) -> logging.Logger:
        log_dir = os.path.join(ROOT_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f"{self.PLATFORM}.log")),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger(self.PLATFORM)

    # ---- HTTP 客户端 ----

    async def api_get(self, path: str, **kwargs) -> Dict[str, Any]:
        """向核心服务器发送 GET 请求。"""
        url = f"{self.server_url}{path}"
        self._inject_internal_token(kwargs, path=path)
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, **kwargs) as resp:
                return await self._parse_response(resp)

    async def api_post(self, path: str, **kwargs) -> Dict[str, Any]:
        """向核心服务器发送 POST 请求。"""
        url = f"{self.server_url}{path}"
        self._inject_internal_token(kwargs, path=path)
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, **kwargs) as resp:
                return await self._parse_response(resp)

    def _extract_actor_user_id(self, path: str, kwargs: Dict[str, Any]) -> str | None:
        payload = kwargs.get("json")
        if isinstance(payload, dict):
            actor_user_id = payload.get("user_id")
            if actor_user_id:
                return str(actor_user_id)
        params = kwargs.get("params")
        if isinstance(params, dict):
            actor_user_id = params.get("user_id")
            if actor_user_id:
                return str(actor_user_id)
        normalized = str(path or "").split("?", 1)[0]
        for pattern in _ACTOR_PATH_PATTERNS:
            matched = pattern.match(normalized)
            if matched:
                return str(matched.group(1))
        return None

    def _inject_internal_token(self, kwargs: Dict[str, Any], *, path: str = "") -> None:
        headers = dict(kwargs.get("headers") or {})
        if self.internal_api_token:
            headers.setdefault("X-Internal-Token", self.internal_api_token)
        actor_user_id = self._extract_actor_user_id(path, kwargs)
        if actor_user_id:
            headers.setdefault("X-Actor-User-Id", actor_user_id)
        kwargs["headers"] = headers

    async def _parse_response(self, resp: aiohttp.ClientResponse) -> Dict[str, Any]:
        """解析 HTTP 响应为 JSON。"""
        try:
            return await resp.json(content_type=None)
        except Exception:
            text = await resp.text()
            try:
                return json.loads(text)
            except Exception:
                return {
                    "success": False,
                    "code": "NON_JSON_RESPONSE",
                    "message": "Core returned non-JSON response",
                    "status_code": int(getattr(resp, "status", 0) or 0),
                    "raw_text": text[:500],
                }

    # ---- 语言偏好 ----

    def get_lang(self, user_id: str, default: str = "CHS") -> str:
        return "CHS"

    def set_lang(self, user_id: str, lang: str) -> None:
        return None

    # ---- 版本信息 ----

    @property
    def version_string(self) -> str:
        core_ver = os.getenv("CORE_VERSION", "DEV")
        return f"Core-{core_ver} ({self.PLATFORM.title()} Adapter {self.ADAPTER_VERSION})"

    # ---- 抽象方法 ----

    @abstractmethod
    async def start(self) -> None:
        """启动适配器。"""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """停止适配器。"""
        ...

    @abstractmethod
    async def send_message(self, channel_id: str, text: str, **kwargs) -> None:
        """向指定频道/会话发送消息。"""
        ...

    @abstractmethod
    async def reply(self, context: Any, text: str, **kwargs) -> None:
        """回复当前上下文中的消息。"""
        ...

    @abstractmethod
    def register_commands(self) -> None:
        """注册所有命令处理器。"""
        ...

    @abstractmethod
    def get_token(self) -> str:
        """获取平台 Token。"""
        ...
