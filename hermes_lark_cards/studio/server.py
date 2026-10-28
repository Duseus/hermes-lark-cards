"""Visual Card Studio — Zero-dependency HTTP Backend.

Provides:
- GET  /api/config      -> Read effective streaming config
- POST /api/config      -> Deep-merge UI-managed keys into config.yaml
- GET  /api/presets     -> Return built-in visual presets (Classic, Minimal, Bubble Wave)
- GET  /api/health      -> Liveness & version probe
- POST /api/restart     -> Restart Hermes Gateway via systemctl --user (best-effort)
- Static file serving from hermes_lark_cards/studio/web/ directory
"""

from __future__ import annotations

import copy
import http.server
import json
import logging
import os
import re
import socketserver
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from .. import __version__ as _VERSION
from ..config import Config, _config_path, hermes_home

_logger = logging.getLogger("hermes_lark_cards.studio")

# CardKit 2.0 supported text sizes
_SUPPORTED_TEXT_SIZES = {"heading", "normal_v2", "notation"}
_SUPPORTED_WIDTH_MODES = {"default", "compact", "fill"}

# ── Built-in Visual Presets ──────────────────────────────────────────
PRESETS: dict[str, dict[str, Any]] = {
    "classic": {
        "id": "classic",
        "name": "🏛️ 经典科技 (Classic Tech)",
        "desc": "标准版式。无大标题、紧凑宽度、标准工具折叠与全维指标底栏",
        "config": {
            "enabled": True,
            "width_mode": "default",
            "panel_expanded": False,
            "header": {"enabled": False},
            "body": {"text_size": "normal_v2"},
            "footer": {
                "enabled": True,
                "text_size": "notation",
                "show_label": False,
                "fields": [
                    ["status", "elapsed", "model"],
                    ["tokens", "context"],
                    ["weather"],
                    ["hitokoto"],
                ],
            },
        },
    },
    "bubble_wave": {
        "id": "bubble_wave",
        "name": "🫧 泡波轻灵 (Bubble Wave)",
        "desc": "轻灵活泼。充满卡片模式 (fill)、大标题打字机、高频展开",
        "config": {
            "enabled": True,
            "width_mode": "fill",
            "panel_expanded": False,
            "header": {"enabled": True},
            "body": {"text_size": "normal_v2"},
            "footer": {
                "enabled": True,
                "text_size": "notation",
                "show_label": False,
                "fields": [
                    ["status", "elapsed", "context", "model"],
                    ["weather", "hitokoto"],
                ],
            },
        },
    },
    "minimal": {
        "id": "minimal",
        "name": "🍃 极简极速 (Minimalist)",
        "desc": "极度克制。紧凑模式 (compact)，折叠工具，仅保留耗时与模型",
        "config": {
            "enabled": True,
            "width_mode": "compact",
            "panel_expanded": False,
            "header": {"enabled": False},
            "body": {"text_size": "normal_v2"},
            "footer": {
                "enabled": True,
                "text_size": "notation",
                "show_label": False,
                "fields": [
                    ["elapsed", "model"],
                ],
            },
        },
    },
}

UI_MANAGED_KEYS = (
    "enabled",
    "width_mode",
    "panel_expanded",
    "card_ttl_sec",
    "header",
    "body",
    "footer",
)


class ConfigReadError(Exception):
    """Raised when config.yaml cannot be parsed safely."""


def read_full_config() -> dict[str, Any]:
    cfg_file = _config_path()
    if not cfg_file.exists():
        return {}
    try:
        text = cfg_file.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigReadError(f"无法读取 {cfg_file}: {e}") from e
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ConfigReadError(f"{cfg_file} YAML 解析失败: {e}") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigReadError(f"{cfg_file} 顶层结构必须是映射，实际为 {type(data).__name__}")
    return data


def _validate_ui_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "载荷必须是 JSON 对象"

    if "width_mode" in payload and payload["width_mode"] not in _SUPPORTED_WIDTH_MODES:
        return False, f"不支持的 width_mode: {payload['width_mode']}"

    if "header" in payload:
        header = payload["header"]
        if not isinstance(header, dict):
            return False, "header 必须是对象"
        if "enabled" in header and not isinstance(header["enabled"], bool):
            return False, "header.enabled 必须是布尔值"
        if "title" in header and not isinstance(header["title"], str):
            return False, "header.title 必须是字符串"

    if "body" in payload:
        body = payload["body"]
        if not isinstance(body, dict):
            return False, "body 必须是对象"
        if "text_size" in body and body["text_size"] not in _SUPPORTED_TEXT_SIZES:
            return False, f"不支持的 body.text_size: {body['text_size']}"

    if "footer" in payload:
        footer = payload["footer"]
        if not isinstance(footer, dict):
            return False, "footer 必须是对象"
        if "enabled" in footer and not isinstance(footer["enabled"], bool):
            return False, "footer.enabled 必须是布尔值"
        if "text_size" in footer and footer["text_size"] not in _SUPPORTED_TEXT_SIZES:
            return False, f"不支持的 footer.text_size: {footer['text_size']}"
        if "fields" in footer:
            fields = footer["fields"]
            if not isinstance(fields, list):
                return False, "footer.fields 必须是列表"
            for row in fields:
                if not isinstance(row, list) or not all(isinstance(f, str) for f in row):
                    return False, "footer.fields 必须是二维字符串数组"

    return True, ""


def write_streaming_config(ui_cfg: dict[str, Any]) -> tuple[bool, str]:
    ok, err = _validate_ui_payload(ui_cfg)
    if not ok:
        return False, err

    cfg_file = _config_path()
    try:
        full_cfg = read_full_config()
    except ConfigReadError as e:
        return False, f"拒绝写入：现有配置无法解析，请先修复。{e}"

    cfg_file.parent.mkdir(parents=True, exist_ok=True)

    # 备份现有配置
    if cfg_file.exists():
        backup_dir = cfg_file.parent / "backups" / "studio_config_baks"
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"config.yaml.bak_{ts}"
            backup_path.write_text(cfg_file.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError as e:
            _logger.warning("Failed to create studio backup: %s", e)

    # 深度合并 streaming 配置
    existing_streaming = full_cfg.get("streaming") or {}
    if not isinstance(existing_streaming, dict):
        existing_streaming = {}
    merged_streaming = copy.deepcopy(existing_streaming)

    for key in UI_MANAGED_KEYS:
        if key not in ui_cfg:
            continue
        val = ui_cfg[key]
        if isinstance(val, dict) and isinstance(merged_streaming.get(key), dict):
            merged_streaming[key] = {**merged_streaming[key], **val}
        else:
            merged_streaming[key] = val

    full_cfg["streaming"] = merged_streaming

    try:
        dumped = yaml.safe_dump(full_cfg, sort_keys=False, allow_unicode=True)
        tmp_path = cfg_file.with_suffix(".tmp")
        tmp_path.write_text(dumped, encoding="utf-8")
        tmp_path.replace(cfg_file)
    except OSError as e:
        return False, f"写入配置文件失败: {e}"

    return True, "配置保存成功"


class StudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Studio Request Handler serving APIs and frontend static files."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        web_dir = Path(__file__).parent / "web"
        super().__init__(*args, directory=str(web_dir), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json(200, {"ok": True, "version": _VERSION, "status": "running"})
            return
        if self.path == "/api/presets":
            self._send_json(200, PRESETS)
            return
        if self.path == "/api/config":
            self._handle_get_config()
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/config":
            self._handle_post_config()
            return
        if self.path == "/api/restart":
            self._handle_restart_gateway()
            return
        self._send_json(404, {"ok": False, "error": f"Unknown endpoint {self.path}"})

    def _handle_get_config(self) -> None:
        cfg = Config()
        sec = cfg._streaming_sec()
        effective = {
            "enabled": cfg.enabled,
            "width_mode": cfg.width_mode,
            "panel_expanded": cfg.panel_expanded,
            "card_ttl_sec": cfg.card_duration_sec,
            "header": {
                "enabled": cfg.header_enabled,
                "title": cfg.header_title,
            },
            "body": {
                "text_size": cfg.body_text_size,
            },
            "footer": {
                "enabled": cfg.footer_enabled,
                "text_size": cfg.footer_text_size,
                "show_label": cfg.footer_show_label,
                "fields": cfg.footer_fields,
            },
            "show_reasoning": cfg.show_reasoning,
            "show_tool_use": cfg.show_tool_use,
        }
        self._send_json(200, {"ok": True, "config": effective, "raw_streaming": sec})

    def _handle_post_config(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body)
        except Exception as e:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {e}"})
            return

        ok, msg = write_streaming_config(payload)
        if ok:
            self._send_json(200, {"ok": True, "message": msg})
        else:
            self._send_json(400, {"ok": False, "error": msg})

    def _handle_restart_gateway(self) -> None:
        try:
            res = subprocess.run(
                ["systemctl", "--user", "restart", "hermes-gateway"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0:
                self._send_json(200, {"ok": True, "restarted": True, "message": "Hermes Gateway 重启成功"})
            else:
                self._send_json(500, {"ok": False, "error": f"重启失败: {res.stderr.strip()}"})
        except FileNotFoundError:
            self._send_json(200, {"ok": True, "restarted": False, "message": "系统未安装 systemctl，配置已保存"})
        except Exception as e:
            self._send_json(500, {"ok": False, "error": str(e)})

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        _logger.debug("Studio: " + (format % args))


class _StudioServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_studio_server(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> int:
    try:
        httpd = _StudioServer((host, port), StudioRequestHandler)
    except OSError as e:
        print(f"\n[Visual Studio] 无法在 {host}:{port} 启动服务：{e}")
        print("  端口可能被占用，请指定其它端口，例如: hermes-lark-cards studio --port 8770\n")
        return 1

    with httpd:
        url = f"http://{host}:{port}"
        print("\n=======================================================")
        print(f"  🎨 hermes-lark-cards Visual Studio (v{_VERSION})")
        print("  🎴 飞书 CardKit 2.0 流式卡片可视化工作坊")
        print("  -----------------------------------------------------")
        print(f"  🌐 服务地址: {url}")
        print(f"  📂 配置文件: {_config_path()}")
        print("  🔒 仅监听本机回环地址（loopback-only）")
        print("  ⌨️  按 Ctrl+C 退出工作坊")
        print("=======================================================\n")

        if open_browser:
            import webbrowser
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStudio 服务已平稳停止。")
    return 0
