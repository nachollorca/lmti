"""Tests for lmti.config."""

import os
import stat
from pathlib import Path

import yaml

from lmti.config import AUTH_PATH, AVAILABLE_MODELS, SETTINGS_PATH, Config


def test_load_creates_default_when_missing(tmp_path):
    settings_path = tmp_path / "lmti.yaml"
    auth_path = tmp_path / "auth.yaml"
    config = Config.load(settings_path=settings_path, auth_path=auth_path)
    assert settings_path.exists()
    assert not auth_path.exists()
    assert config.settings.model == "mistral:mistral-small-2603"
    assert config.models == AVAILABLE_MODELS


def test_save_and_load_roundtrip(tmp_path):
    settings_path = tmp_path / "lmti.yaml"
    auth_path = tmp_path / "auth.yaml"
    config = Config()
    config.settings.render_markdown = False
    config.settings.model = "mistral:devstral-2512"
    config.credentials = {"FOO_KEY": "abc"}
    config.save(settings_path=settings_path, auth_path=auth_path)

    loaded = Config.load(settings_path=settings_path, auth_path=auth_path)
    assert loaded.settings.render_markdown is False
    assert loaded.settings.model == "mistral:devstral-2512"
    assert loaded.credentials == {"FOO_KEY": "abc"}


def test_kebab_case_system_instruction_alias(tmp_path):
    settings_path = tmp_path / "lmti.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(yaml.dump({"settings": {"system-instruction": "be brief"}}))
    config = Config.load(settings_path=settings_path, auth_path=tmp_path / "auth.yaml")
    assert config.settings.system_instruction == "be brief"


def test_models_drift_triggers_resave(tmp_path):
    settings_path = tmp_path / "lmti.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(yaml.dump({"models": ["old:model"]}))
    config = Config.load(settings_path=settings_path, auth_path=tmp_path / "auth.yaml")
    # Custom models are preserved, hardcoded models are prepended
    assert config.models == [*AVAILABLE_MODELS, "old:model"]
    persisted = yaml.safe_load(settings_path.read_text())
    assert persisted["models"] == [*AVAILABLE_MODELS, "old:model"]


def test_corrupt_yaml_falls_back_to_defaults(tmp_path):
    settings_path = tmp_path / "lmti.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("not: valid: yaml: [[[")
    config = Config.load(settings_path=settings_path, auth_path=tmp_path / "auth.yaml")
    assert config.settings.model == "mistral:mistral-small-2603"


def test_set_api_key_writes_env_and_file(tmp_path, monkeypatch):
    settings_path = tmp_path / "lmti.yaml"
    auth_path = tmp_path / "auth.yaml"
    real_save = Config.save
    monkeypatch.setattr(
        Config,
        "save",
        lambda self, sp=settings_path, ap=auth_path: real_save(
            self, settings_path=sp, auth_path=ap
        ),
    )
    monkeypatch.delenv("MY_KEY", raising=False)
    config = Config()
    config.set_api_key("MY_KEY", "secret")
    assert os.environ["MY_KEY"] == "secret"
    assert config.credentials["MY_KEY"] == "secret"
    persisted = yaml.safe_load(auth_path.read_text())
    assert persisted["MY_KEY"] == "secret"
    assert auth_path.stat().st_mode & 0o777 == stat.S_IRUSR | stat.S_IWUSR


def test_load_injects_credentials_into_env(tmp_path, monkeypatch):
    auth_path = tmp_path / "auth.yaml"
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(yaml.dump({"INJECTED_KEY": "v1"}))
    settings_path = tmp_path / "lmti.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(yaml.dump({"settings": {}, "models": list(AVAILABLE_MODELS)}))
    monkeypatch.delenv("INJECTED_KEY", raising=False)
    Config.load(settings_path=settings_path, auth_path=auth_path)
    assert os.environ["INJECTED_KEY"] == "v1"


def test_default_paths():
    assert Path.home() / ".config" / "lmti.yaml" == SETTINGS_PATH
    assert Path.home() / ".lmti" / "auth.yaml" == AUTH_PATH
