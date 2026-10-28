"""模型与状态的飞书图标（standard_icon 与 custom_icon）与主题映射.

CardKit 2.0 折叠面板 header.icon 支持两种配置模式：
1. custom_icon: 使用通过飞书上传获取的 img_key（例如官方高清全彩矢量/PNG 图标），具有极高质感与品牌还原度。
2. standard_icon: 无需上传直接使用飞书内置标准图标（如 whale_outlined, sparks_outlined 等）。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..feishu import FeishuClient

_logger = logging.getLogger("hermes_lark_cards")

# 模型名关键词 -> 对应的资源文件名（优先于 standard_icon）
MODEL_CUSTOM_ASSET_MAPPING: list[tuple[str, str]] = [
    ("gemini", "gemini-color.png"),
    ("deepseek", "deepseek-color.png"),
    ("claude", "claude-color.png"),
    ("gpt", "openai-color.png"),
    ("openai", "openai-color.png"),
    ("o1", "openai-color.png"),
    ("o3", "openai-color.png"),
    ("o4", "openai-color.png"),
    ("qwen", "qwen-color.png"),
    ("kimi", "kimi-color.png"),
    ("glm", "chatglm-color.png"),
    ("swe", "devin-color.png"),
    ("devin", "devin-color.png"),
    ("cognition", "devin-color.png"),
]

# 模型名子串 -> 飞书 standard_icon 配置（未上传或回退时使用）
MODEL_ICON_MAPPING: list[tuple[str, dict[str, str]]] = [
    ("deepseek", {"token": "whale_outlined", "color": "blue"}),
    ("claude", {"token": "sparks_outlined", "color": "orange"}),
    ("gpt", {"token": "connect_outlined", "color": "green"}),
    ("openai", {"token": "connect_outlined", "color": "green"}),
    ("o1", {"token": "connect_outlined", "color": "green"}),
    ("o3", {"token": "connect_outlined", "color": "green"}),
    ("o4", {"token": "connect_outlined", "color": "green"}),
    ("gemini", {"token": "star-shine_outlined", "color": "blue"}),
    ("qwen", {"token": "lightning_outlined", "color": "purple"}),
    ("kimi", {"token": "send_outlined", "color": "blue"}),
    ("glm", {"token": "mind-mapping_outlined", "color": "blue"}),
    ("doubao", {"token": "chat_outlined", "color": "blue"}),
    ("minimax", {"token": "voice_outlined", "color": "blue"}),
    ("swe", {"token": "ai-agent_outlined", "color": "purple"}),
    ("devin", {"token": "ai-agent_outlined", "color": "purple"}),
    ("cognition", {"token": "ai-agent_outlined", "color": "purple"}),
]

DEFAULT_PANEL_ICON: dict[str, str] = {
    "token": "down-small-ccm_outlined",
    "color": "grey",
}

# 运行时内存缓存：asset_filename -> img_key
_ASSET_IMG_KEY_CACHE: dict[str, str] = {}


def get_icon_asset_path(filename: str) -> Path | None:
    """获取内置图标文件的绝对路径."""
    candidates = [
        Path(__file__).parent.parent / "assets" / "icons" / filename,
        Path(__file__).parent.parent.parent / "assets" / "icons" / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _get_cache_file_path() -> Path:
    """获取本地持久化缓存文件路径（~/.hermes/card_icons_cache.json）."""
    try:
        from ..config import hermes_home

        home = hermes_home()
    except Exception:
        home = Path.home() / ".hermes"
    home.mkdir(parents=True, exist_ok=True)
    return home / "card_icons_cache.json"


def _load_persisted_cache() -> dict[str, str]:
    """从磁盘加载 img_key 缓存."""
    cache_file = _get_cache_file_path()
    if cache_file.is_file():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            _logger.debug("Failed to read icon cache file", exc_info=True)
    return {}


def _save_persisted_cache(cache: dict[str, str]) -> None:
    """持久化 img_key 缓存到磁盘."""
    cache_file = _get_cache_file_path()
    try:
        cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        _logger.debug("Failed to save icon cache file", exc_info=True)


async def resolve_model_img_key(
    model_name: str | None,
    client: FeishuClient | None = None,
) -> str | None:
    """根据模型名称尝试解析或上传对应的高清品牌图标，返回 img_key."""
    if not model_name:
        return None

    name = model_name.lower()
    asset_file: str | None = None
    for keyword, filename in MODEL_CUSTOM_ASSET_MAPPING:
        if keyword in name:
            asset_file = filename
            break

    if not asset_file:
        return None

    # 1. 检查内存缓存
    if asset_file in _ASSET_IMG_KEY_CACHE:
        return _ASSET_IMG_KEY_CACHE[asset_file]

    # 2. 检查磁盘持久化缓存
    persisted = _load_persisted_cache()
    if asset_file in persisted:
        _ASSET_IMG_KEY_CACHE[asset_file] = persisted[asset_file]
        return persisted[asset_file]

    # 3. 若提供 client，则读取本地文件并上传飞书
    if client is not None:
        asset_path = get_icon_asset_path(asset_file)
        if asset_path and asset_path.is_file():
            try:
                data = asset_path.read_bytes()
                img_key = await client.upload_image_bytes(data)
                if img_key:
                    _ASSET_IMG_KEY_CACHE[asset_file] = img_key
                    persisted[asset_file] = img_key
                    _save_persisted_cache(persisted)
                    _logger.info("Successfully uploaded brand icon %s -> %s", asset_file, img_key)
                    return img_key
            except Exception:
                _logger.warning("Failed to upload brand icon %s", asset_file, exc_info=True)

    return None


def resolve_model_icon(model_name: str | None) -> dict[str, str]:
    """根据模型名称匹配专属的飞书右侧指示图标 (标准图标)."""
    if not model_name:
        return dict(DEFAULT_PANEL_ICON)
    name = model_name.lower()
    for keyword, icon_cfg in MODEL_ICON_MAPPING:
        if keyword in name:
            return dict(icon_cfg)
    return dict(DEFAULT_PANEL_ICON)
