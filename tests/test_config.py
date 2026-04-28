"""Tests for lmti.config."""

import os

import yaml

from lmti.config import AVAILABLE_MODELS, Config


def test_load_creates_default_when_missing(tmp_path):
    path = tmp_path / "config.yaml"
    config = Config.load(path)
    assert path.exists()
    assert config.settings.model == "mistral:mistral-small-2603"
    assert config.models == AVAILABLE_MODELS


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "config.yaml"
    config = Config()
    config.settings.render_markdown = False
    config.settings.model = "mistral:devstral-2512"
    config.credentials = {"FOO_KEY": "abc"}
    config.save(path)

    loaded = Config.load(path)
    assert loaded.settings.render_markdown is False
    assert loaded.settings.model == "mistral:devstral-2512"
    assert loaded.credentials == {"FOO_KEY": "abc"}


def test_kebab_case_system_instruction_alias(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump({"settings": {"system-instruction": "be brief"}}))
    config = Config.load(path)
    assert config.settings.system_instruction == "be brief"


def test_models_drift_triggers_resave(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump({"models": ["old:model"]}))
    config = Config.load(path)
    assert config.models == AVAILABLE_MODELS
    # Re-read raw to confirm it was persisted.
    persisted = yaml.safe_load(path.read_text())
    assert persisted["models"] == AVAILABLE_MODELS


def test_corrupt_yaml_falls_back_to_defaults(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("not: valid: yaml: [[[")
    config = Config.load(path)
    assert config.settings.model == "mistral:mistral-small-2603"


def test_set_api_key_writes_env_and_file(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    # Default args are bound at def-time, so module-attr patching of CONFIG_PATH
    # is not enough — redirect Config.save() to our tmp path instead.
    real_save = Config.save
    monkeypatch.setattr(Config, "save", lambda self, p=path: real_save(self, p))
    monkeypatch.delenv("MY_KEY", raising=False)
    config = Config()
    config.set_api_key("MY_KEY", "secret")
    assert os.environ["MY_KEY"] == "secret"
    assert config.credentials["MY_KEY"] == "secret"
    persisted = yaml.safe_load(path.read_text())
    assert persisted["credentials"]["MY_KEY"] == "secret"


def test_load_injects_credentials_into_env(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump({"credentials": {"INJECTED_KEY": "v1"}}))
    monkeypatch.delenv("INJECTED_KEY", raising=False)
    Config.load(path)
    assert os.environ["INJECTED_KEY"] == "v1"
