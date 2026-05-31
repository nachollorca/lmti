"""Tests for /model."""

from lmti.commands.model import _get_manual_model, handle_model
from lmti.config import Config


def test_get_manual_model_cancel(console, fake_prompt):
    fake_prompt([""])
    assert _get_manual_model(console) is None


def test_get_manual_model_rejects_then_accepts(console, fake_prompt):
    fake_prompt(["bad", "provider:", ":model", "vertex:gemini-2.5-flash"])
    assert _get_manual_model(console) == "vertex:gemini-2.5-flash"


def test_handle_model_cancel(console, monkeypatch, config_paths):
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: None)
    config = Config()
    before = config.settings.model
    handle_model(console, config)
    assert config.settings.model == before


def test_handle_model_pick_index(console, monkeypatch, config_paths):
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: 2)
    config = Config()
    handle_model(console, config)
    assert config.settings.model == config.models[1]


def test_handle_model_manual(console, monkeypatch, config_paths, fake_prompt):
    monkeypatch.setattr(
        "lmti.ui.prompt_selection",
        lambda *a, **k: "Add a manual model identifier",
    )
    fake_prompt(["custom:thing"])
    config = Config()
    handle_model(console, config)
    assert config.settings.model == "custom:thing"


def test_handle_model_unknown_string_selection(console, monkeypatch, config_paths):
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: "unexpected")
    config = Config()
    before = config.settings.model
    handle_model(console, config)
    assert config.settings.model == before


def test_handle_model_manual_cancel(console, monkeypatch, config_paths, fake_prompt):
    monkeypatch.setattr(
        "lmti.ui.prompt_selection",
        lambda *a, **k: "Add a manual model identifier",
    )
    fake_prompt([""])
    config = Config()
    before = config.settings.model
    handle_model(console, config)
    assert config.settings.model == before
