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
