"""模型与状态的飞书标准图标（standard_icon）与主题映射.

CardKit 2.0 折叠面板 header.icon 支持指定飞书官方 standard_icon token：
- DeepSeek: 蓝鲸/海洋图标 (whale_outlined / global-feature-link_outlined)
- Claude: 智能火花/星光图标 (sparks_outlined / star_outlined)
- OpenAI / GPT: 神经网络/网格图标 (connect_outlined / apps_outlined)
- Gemini: 四角星 (star-shine_outlined / star_outlined)
- Qwen / 通义千问: 闪电灵动 (lightning_outlined / bot_outlined)
- Fallback: 下拉小箭头 (down-small-ccm_outlined) 或小机器人 (bot_outlined)
"""

from __future__ import annotations

from typing import Any

# 模型名子串 -> 飞书 standard_icon 配置
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
]

DEFAULT_PANEL_ICON: dict[str, str] = {
    "token": "down-small-ccm_outlined",
    "color": "grey",
}


def resolve_model_icon(model_name: str | None) -> dict[str, str]:
    """根据模型名称匹配专属的飞书右侧指示图标."""
    if not model_name:
        return dict(DEFAULT_PANEL_ICON)
    name = model_name.lower()
    for keyword, icon_cfg in MODEL_ICON_MAPPING:
        if keyword in name:
            return dict(icon_cfg)
    return dict(DEFAULT_PANEL_ICON)
