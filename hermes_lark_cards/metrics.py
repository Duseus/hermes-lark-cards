"""指标格式化与外部小数据源（天气 / 一言）.

全部使用标准库，不引入额外依赖；任何网络失败都静默降级，绝不阻塞回复。
支持动态模型别名（如峰谷价切换）以及天气与一言展示。
"""

from __future__ import annotations

import json
import random
import time
import urllib.request
from contextlib import suppress
from typing import Any

DEFAULT_CONTEXT_WINDOW = 200_000

# 备用句子：一言接口不可用时兜底，避免底栏缺行
HITOKOTO_FALLBACK = [
    "保持好奇，持续折腾。",
    "慢慢来，比较快。",
    "把事办利索，比说得好听重要。",
    "所有的捷径，最后都绕远了。",
]

_WEATHER_CACHE: dict[str, Any] = {"ts": 0.0, "text": "", "ttl": 300.0, "key": None}
_HITOKOTO_CACHE: dict[str, Any] = {"ts": 0.0, "text": "", "ttl": 900.0}

# 默认坐标（临平），可通过配置文件或环境变量覆盖
WEATHER_LATITUDE = 30.42
WEATHER_LONGITUDE = 120.30
WEATHER_PLACE = "临平"


def compact_num(value: int | float) -> str:
    """12345 → 12.3K；1234567 → 1.2M."""
    value = int(value or 0)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def footer_elapsed(seconds: float) -> str:
    """底栏耗时：6.4s / 4m 11s."""
    seconds = max(float(seconds or 0.0), 0.0)
    if seconds >= 60:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    return f"{seconds:.1f}s"


def human_duration(seconds: float) -> str:
    """面板标题耗时：7.7 秒 / 10 分 9 秒."""
    seconds = max(float(seconds or 0.0), 0.0)
    if seconds >= 60:
        minutes = int(seconds // 60)
        rest = round(seconds - minutes * 60)
        if rest >= 60:
            minutes += 1
            rest = 0
        return f"{minutes} 分 {rest} 秒"
    return f"{seconds:.1f} 秒"


# 常用模型上下文窗口映射
FALLBACK_WINDOWS: tuple[tuple[str, int], ...] = (
    ("gemini", 1_048_576),
    ("gpt-5", 400_000),
    ("deepseek-v4", 1_048_576),
    ("deepseek", 64_000),
    ("kimi", 262_144),
    ("claude", 200_000),
    ("glm", 200_000),
    ("qwen", 128_000),
)


def resolve_context_window(model: str | None) -> int:
    """解析模型上下文窗口."""
    name = (model or "").lower()
    for keyword, window in FALLBACK_WINDOWS:
        if keyword in name:
            return window
    return DEFAULT_CONTEXT_WINDOW


def format_model_name(model_name: str | None, alias_map: dict[str, str] | None = None) -> str:
    """格式化模型名称，支持峰谷价/自定义别名映射."""
    if not model_name:
        return ""
    if alias_map and model_name in alias_map:
        return alias_map[model_name]
    return model_name


def _weather_icon(code: int) -> str:
    if code in (0, 1):
        return "☀️"
    if code == 2:
        return "⛅"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "🌫️"
    if code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "🌧️"
    if code in (71, 73, 75, 85, 86):
        return "🌨️"
    if code in (95, 96, 99):
        return "⛈️"
    return "🌡️"


def weather_cache_key(lat: float, lon: float, place: str) -> str:
    return f"{lat:.4f},{lon:.4f},{place}"


def cached_weather_text(
    lat: float = WEATHER_LATITUDE, lon: float = WEATHER_LONGITUDE, place: str = WEATHER_PLACE
) -> str:
    """只读天气缓存；未命中返回空串，绝不发网络请求。

    完成态卡片是在 async 热路径上构建的，同步 urlopen 会阻塞事件循环。
    """
    now = time.time()
    key = weather_cache_key(lat, lon, place)
    if _WEATHER_CACHE.get("key") not in (None, key):
        return ""
    if now - float(_WEATHER_CACHE.get("ts") or 0) >= float(_WEATHER_CACHE.get("ttl") or 300):
        return ""
    return str(_WEATHER_CACHE.get("text") or "")


def cached_hitokoto_text() -> str:
    """只读一言缓存；未命中返回空串。"""
    now = time.time()
    if now - float(_HITOKOTO_CACHE.get("ts") or 0) >= float(_HITOKOTO_CACHE.get("ttl") or 900):
        return ""
    return str(_HITOKOTO_CACHE.get("text") or "")


def prefetch_footer_metrics(
    lat: float = WEATHER_LATITUDE, lon: float = WEATHER_LONGITUDE, place: str = WEATHER_PLACE
) -> None:
    """后台预取天气与一言（同步实现，供 to_thread 调用），失败静默。"""
    with suppress(Exception):
        fetch_weather(lat, lon, place)
    with suppress(Exception):
        fetch_hitokoto()


async def prefetch_footer_metrics_async(
    lat: float = WEATHER_LATITUDE, lon: float = WEATHER_LONGITUDE, place: str = WEATHER_PLACE
) -> None:
    """不阻塞事件循环的后台预取。"""
    import asyncio

    await asyncio.to_thread(prefetch_footer_metrics, lat, lon, place)


def fetch_weather(lat: float = WEATHER_LATITUDE, lon: float = WEATHER_LONGITUDE, place: str = WEATHER_PLACE) -> str:
    """实时天气（open-meteo，免费无 Key），默认缓存 5 分钟."""
    now = time.time()
    key = weather_cache_key(lat, lon, place)
    same_key = _WEATHER_CACHE.get("key") in (None, key)
    if (
        same_key
        and _WEATHER_CACHE.get("text")
        and now - float(_WEATHER_CACHE.get("ts") or 0) < float(_WEATHER_CACHE.get("ttl") or 300)
    ):
        return str(_WEATHER_CACHE["text"])
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,relative_humidity_2m"
        "&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset"
        "&timezone=Asia/Shanghai&forecast_days=1"
    )
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "hermes-lark-cards"})
        with urllib.request.urlopen(request, timeout=5) as response:
            data = json.loads(response.read())
        current = data.get("current", {})
        daily = data.get("daily", {})
        icon = _weather_icon(int(current.get("weather_code", 0) or 0))
        t_max = (daily.get("temperature_2m_max") or [""])[0]
        t_min = (daily.get("temperature_2m_min") or [""])[0]
        humidity = current.get("relative_humidity_2m", "")
        text = f"{icon} {place} {t_max}°C/{t_min}°C · 湿度 {humidity}%"
        _WEATHER_CACHE["ts"] = now
        _WEATHER_CACHE["text"] = text
        _WEATHER_CACHE["key"] = key
        return text
    except Exception:
        return str(_WEATHER_CACHE.get("text") or "")


def fetch_hitokoto() -> str:
    """一言（文学/哲学/诗词向），失败时用本地句子兜底."""
    url = "https://v1.hitokoto.cn/?c=d&c=k&c=j&c=i&max_length=28"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "hermes-lark-cards"})
        with urllib.request.urlopen(request, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = (data.get("hitokoto") or "").strip()
        source = (data.get("from") or data.get("from_who") or "").strip()
        if text:
            rendered = f"*{text}* —— *{source}*" if source else f"*{text}*"
            _HITOKOTO_CACHE["ts"] = time.time()
            _HITOKOTO_CACHE["text"] = rendered
            return rendered
    except Exception:
        pass
    return f"*{random.choice(HITOKOTO_FALLBACK)}*"
