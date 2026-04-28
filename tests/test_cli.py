"""Tests for lmti.cli."""

import sys

from lmti import cli
from lmti.config import Config


def _stub_load(monkeypatch, config):
    monkeypatch.setattr(cli.Config, "load", classmethod(lambda cls: config))


def test_main_uses_config_default(monkeypatch):
    config = Config()
    _stub_load(monkeypatch, config)
    monkeypatch.setattr(sys, "argv", ["lmti"])
    captured = {}
    monkeypatch.setattr(cli, "run", lambda config: captured.setdefault("config", config))
    cli.main()
    assert captured["config"] is config
    assert captured["config"].settings.model == "mistral:mistral-small-2603"


def test_main_overrides_model_from_cli(monkeypatch):
    config = Config()
    _stub_load(monkeypatch, config)
    monkeypatch.setattr(sys, "argv", ["lmti", "-m", "vertex:gemini-2.5-flash"])
    captured = {}
    monkeypatch.setattr(cli, "run", lambda config: captured.setdefault("config", config))
    cli.main()
    assert captured["config"].settings.model == "vertex:gemini-2.5-flash"


def test_main_loads_existing_config_default(monkeypatch):
    config = Config()
    config.settings.model = "anthropic:claude-haiku-4-5"
    _stub_load(monkeypatch, config)
    monkeypatch.setattr(sys, "argv", ["lmti"])
    captured = {}
    monkeypatch.setattr(cli, "run", lambda config: captured.setdefault("config", config))
    cli.main()
    assert captured["config"].settings.model == "anthropic:claude-haiku-4-5"
