"""Tests for hermes_lark_cards.studio."""

import json
from pathlib import Path
from unittest.mock import patch

import yaml

from hermes_lark_cards.studio.server import (
    PRESETS,
    _validate_ui_payload,
    read_full_config,
    write_streaming_config,
)


def test_presets_structure():
    assert "classic" in PRESETS
    assert "bubble_wave" in PRESETS
    assert "minimal" in PRESETS
    for p in PRESETS.values():
        assert "id" in p
        assert "name" in p
        assert "config" in p
        assert isinstance(p["config"], dict)


def test_validate_ui_payload():
    valid_payload = {
        "width_mode": "compact",
        "header": {"enabled": True},
        "body": {"text_size": "normal_v2"},
        "footer": {
            "enabled": True,
            "text_size": "notation",
            "fields": [["status", "elapsed"]],
        },
    }
    ok, err = _validate_ui_payload(valid_payload)
    assert ok is True
    assert err == ""

    # Invalid width mode
    ok, err = _validate_ui_payload({"width_mode": "ultra-wide"})
    assert ok is False

    # Invalid text size
    ok, err = _validate_ui_payload({"body": {"text_size": "invalid_size"}})
    assert ok is False

    # Invalid footer fields
    ok, err = _validate_ui_payload({"footer": {"fields": "not-a-list"}})
    assert ok is False


def test_write_streaming_config(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.yaml"
    initial_content = {
        "gateway": {"platforms": {"feishu": {"extra": {"app_id": "test_id"}}}},
        "streaming": {"enabled": False, "width_mode": "default"},
    }
    cfg_file.write_text(yaml.safe_dump(initial_content), encoding="utf-8")

    monkeypatch.setattr("hermes_lark_cards.studio.server._config_path", lambda: cfg_file)

    ui_cfg = {
        "enabled": True,
        "width_mode": "fill",
        "header": {"enabled": True},
        "footer": {
            "enabled": True,
            "text_size": "notation",
            "fields": [["status", "model"]],
        },
    }

    ok, msg = write_streaming_config(ui_cfg)
    assert ok is True

    # Read back and verify deep merge preserves unrelated gateway config
    saved_cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    assert saved_cfg["gateway"]["platforms"]["feishu"]["extra"]["app_id"] == "test_id"
    assert saved_cfg["streaming"]["enabled"] is True
    assert saved_cfg["streaming"]["width_mode"] == "fill"
    assert saved_cfg["streaming"]["header"]["enabled"] is True
    assert saved_cfg["streaming"]["footer"]["fields"] == [["status", "model"]]

import io
import threading
import time
import urllib.request
import urllib.error
from http.server import HTTPServer
from hermes_lark_cards.studio.server import _StudioServer, StudioRequestHandler


def test_studio_http_server_endpoints(tmp_path, monkeypatch):
    """Test actual HTTP endpoints using a live test server on ephemeral port."""
    cfg_file = tmp_path / "config.yaml"
    initial_content = {
        "gateway": {"platforms": {"feishu": {"extra": {"app_id": "test_id"}}}},
        "streaming": {
            "enabled": True,
            "width_mode": "default",
            "footer": {"fields": [["status", "elapsed"]]},
        },
    }
    cfg_file.write_text(yaml.safe_dump(initial_content), encoding="utf-8")
    monkeypatch.setattr("hermes_lark_cards.studio.server._config_path", lambda: cfg_file)
    monkeypatch.setattr("hermes_lark_cards.config._config_path", lambda home=None: cfg_file)

    # Bind to localhost port 0 (ephemeral port)
    server = _StudioServer(("127.0.0.1", 0), StudioRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. Test Static files
        with urllib.request.urlopen(f"{base_url}/") as res:
            assert res.status == 200
            content = res.read().decode("utf-8")
            assert "Hermes 流式卡片工作坊" in content
            assert "Visual Card Studio" in content

        with urllib.request.urlopen(f"{base_url}/css/style.css") as res:
            assert res.status == 200
            assert "feishu-simulator-wrap" in res.read().decode("utf-8")

        with urllib.request.urlopen(f"{base_url}/js/app.js") as res:
            assert res.status == 200
            assert "StudioApp" in res.read().decode("utf-8")

        with urllib.request.urlopen(f"{base_url}/js/preview.js") as res:
            assert res.status == 200
            assert "CardSimulator" in res.read().decode("utf-8")

        # 2. Test GET /api/health
        with urllib.request.urlopen(f"{base_url}/api/health") as res:
            assert res.status == 200
            data = json.loads(res.read().decode("utf-8"))
            assert data["ok"] is True
            assert data["version"] == "0.3.0"

        # 3. Test GET /api/presets
        with urllib.request.urlopen(f"{base_url}/api/presets") as res:
            assert res.status == 200
            presets = json.loads(res.read().decode("utf-8"))
            assert "classic" in presets
            assert "bubble_wave" in presets

        # 4. Test GET /api/config
        with urllib.request.urlopen(f"{base_url}/api/config") as res:
            assert res.status == 200
            data = json.loads(res.read().decode("utf-8"))
            assert data["ok"] is True
            assert data["config"]["width_mode"] == "default"
            assert data["config"]["enabled"] is True

        # 5. Test POST /api/config (Valid)
        post_data = json.dumps({
            "width_mode": "fill",
            "header": {"enabled": True},
            "footer": {"fields": [["model", "tokens"]]}
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/config",
            data=post_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp_data = json.loads(res.read().decode("utf-8"))
            assert resp_data["ok"] is True

        # Verify config written
        updated_cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        assert updated_cfg["streaming"]["width_mode"] == "fill"
        assert updated_cfg["streaming"]["header"]["enabled"] is True
        assert updated_cfg["streaming"]["footer"]["fields"] == [["model", "tokens"]]

        # 6. Test POST /api/config (Invalid payload)
        bad_post_data = json.dumps({
            "width_mode": "invalid-width-mode"
        }).encode("utf-8")
        bad_req = urllib.request.Request(
            f"{base_url}/api/config",
            data=bad_post_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            urllib.request.urlopen(bad_req)
            assert False, "Should have raised HTTPError"
        except urllib.error.HTTPError as err:
            assert err.code == 400
            body = json.loads(err.read().decode("utf-8"))
            assert body["ok"] is False
            assert "不支持的 width_mode" in body["error"]

        # 7. Test POST /api/restart
        restart_req = urllib.request.Request(
            f"{base_url}/api/restart",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(restart_req) as res:
                data = json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            data = json.loads(err.read().decode("utf-8"))
        assert "message" in data or "error" in data

    finally:
        server.shutdown()
        server.server_close()


def test_custom_header_title_roundtrip(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("streaming:\n  enabled: true\n", encoding="utf-8")
    monkeypatch.setattr("hermes_lark_cards.studio.server._config_path", lambda: cfg_file)

    ui_cfg = {
        "header": {
            "enabled": True,
            "title": "⚡ 智选模型处理中",
        }
    }
    ok, msg = write_streaming_config(ui_cfg)
    assert ok is True

    saved = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    assert saved["streaming"]["header"]["enabled"] is True
    assert saved["streaming"]["header"]["title"] == "⚡ 智选模型处理中"


def test_custom_templates_api_crud(tmp_path, monkeypatch):
    """Test creating, reading, and deleting custom templates."""
    tpl_file = tmp_path / "card_studio_templates.json"
    monkeypatch.setattr("hermes_lark_cards.studio.server._get_templates_file", lambda: tpl_file)

    server = _StudioServer(("127.0.0.1", 0), StudioRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. GET /api/templates (initially empty)
        with urllib.request.urlopen(f"{base_url}/api/templates") as res:
            assert res.status == 200
            data = json.loads(res.read().decode("utf-8"))
            assert data == {}

        # 2. POST /api/templates (Create template)
        save_req = urllib.request.Request(
            f"{base_url}/api/templates",
            data=json.dumps({
                "id": "my_tpl_1",
                "name": "极客监控专属模板",
                "config": {
                    "width_mode": "compact",
                    "footer": {"fields": [["status", "elapsed"]]}
                }
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(save_req) as res:
            assert res.status == 200
            resp_data = json.loads(res.read().decode("utf-8"))
            assert resp_data["ok"] is True
            assert "my_tpl_1" in resp_data["templates"]
            assert resp_data["templates"]["my_tpl_1"]["name"] == "极客监控专属模板"

        # 3. GET /api/templates (Verify persisted)
        with urllib.request.urlopen(f"{base_url}/api/templates") as res:
            data = json.loads(res.read().decode("utf-8"))
            assert "my_tpl_1" in data

        # 4. POST /api/templates/delete (Delete template)
        del_req = urllib.request.Request(
            f"{base_url}/api/templates/delete",
            data=json.dumps({"id": "my_tpl_1"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(del_req) as res:
            assert res.status == 200
            del_data = json.loads(res.read().decode("utf-8"))
            assert del_data["ok"] is True
            assert "my_tpl_1" not in del_data["templates"]

    finally:
        server.shutdown()
        server.server_close()
