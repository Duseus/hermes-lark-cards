"""Tests for CardKit brand icons resolution and caching."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from hermes_lark_cards.cardkit.icons import (
    _ASSET_IMG_KEY_CACHE,
    get_icon_asset_path,
    resolve_model_icon,
    resolve_model_img_key,
)
from hermes_lark_cards.feishu import FeishuClient


def test_resolve_model_icon_standard_tokens() -> None:
    assert resolve_model_icon("deepseek-chat")["token"] == "whale_outlined"
    assert resolve_model_icon("claude-3-5-sonnet")["token"] == "sparks_outlined"
    assert resolve_model_icon("gpt-4o")["token"] == "connect_outlined"
    assert resolve_model_icon("gemini-2.5-flash")["token"] == "star-shine_outlined"
    assert resolve_model_icon("qwen-turbo")["token"] == "lightning_outlined"
    assert resolve_model_icon(None)["token"] == "down-small-ccm_outlined"


def test_get_icon_asset_path() -> None:
    gemini_path = get_icon_asset_path("gemini-color.png")
    assert gemini_path is not None
    assert gemini_path.is_file()
    assert gemini_path.name == "gemini-color.png"


@pytest.mark.asyncio
async def test_resolve_model_img_key_upload_and_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ASSET_IMG_KEY_CACHE.clear()

    cache_file = tmp_path / "card_icons_cache.json"
    monkeypatch.setattr("hermes_lark_cards.cardkit.icons._get_cache_file_path", lambda: cache_file)

    upload_mock = AsyncMock(return_value="img_v3_gemini_brand_key")
    client = FeishuClient.__new__(FeishuClient)
    client.upload_image_bytes = upload_mock

    # 1. 首次解析 Gemini: 触发上传并存入磁盘持久化和内存缓存
    key = await resolve_model_img_key("gemini-2.5-pro", client)
    assert key == "img_v3_gemini_brand_key"
    assert upload_mock.await_count == 1
    assert cache_file.is_file()
    saved = json.loads(cache_file.read_text(encoding="utf-8"))
    assert saved.get("gemini-color.png") == "img_v3_gemini_brand_key"

    # 2. 第二次解析 Gemini (不同模型后缀): 命中内存缓存，不重复上传
    upload_mock.reset_mock()
    key2 = await resolve_model_img_key("gemini-1.5-flash", client)
    assert key2 == "img_v3_gemini_brand_key"
    assert upload_mock.await_count == 0

    # 3. 清空内存缓存测试磁盘缓存重载
    _ASSET_IMG_KEY_CACHE.clear()
    key3 = await resolve_model_img_key("Google-Gemini-Pro", client)
    assert key3 == "img_v3_gemini_brand_key"
    assert upload_mock.await_count == 0

    # 4. 未知模型返回 None
    assert await resolve_model_img_key("unknown-custom-model", client) is None
