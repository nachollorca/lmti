"""Configuration management for lmti.

Settings are stored in ``~/.config/lmti.yaml``.
Credentials are stored in ``~/.lmti/auth.yaml``.
"""

import os
import stat
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

SETTINGS_PATH = Path.home() / ".config" / "lmti.yaml"
AUTH_PATH = Path.home() / ".lmti" / "auth.yaml"
LMTI_DIR = Path.home() / ".lmti"

AVAILABLE_MODELS = [
    "mistral:mistral-small-2603",
    "mistral:mistral-medium-3.5",
    "mistral:devstral-2512",
    "vertex:gemini-2.5-flash",
    "vertex:gemini-3-flash-preview",
    "vertex:gemini-3.1-pro-preview",
    "anthropic:claude-sonnet-4-6",
    "anthropic:claude-opus-4-6",
    "anthropic:claude-haiku-4-5",
]


class Settings(BaseModel):
    """General application settings."""

    render_markdown: bool = True
    model: str = "mistral:mistral-small-2603"
    system_instruction: str | None = Field(default=None, alias="system-instruction")

    model_config = {"populate_by_name": True}  # so we can read kebab case and snake case in yaml


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.dump(data, f, sort_keys=False)


def _secure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


def _secure_file(path: Path) -> None:
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


class Config(BaseModel):
    """Application configuration (settings and credentials)."""

    credentials: dict[str, str] = Field(default_factory=dict)
    settings: Settings = Field(default_factory=Settings)
    models: list[str] = Field(default_factory=lambda: list(AVAILABLE_MODELS))

    @classmethod
    def load(
        cls,
        settings_path: Path = SETTINGS_PATH,
        auth_path: Path = AUTH_PATH,
    ) -> "Config":
        """Load configuration from disk, creating defaults if missing.

        Credentials are injected into ``os.environ``.
        """
        if not settings_path.exists():
            config = cls()
            config.save(settings_path=settings_path, auth_path=auth_path)
            return config

        try:
            data = yaml.safe_load(settings_path.read_text()) or {}
            config = cls(
                settings=Settings(**(data.get("settings") or {})),
                models=data.get("models") or list(AVAILABLE_MODELS),
            )

            # Merge custom models: keep AVAILABLE_MODELS, append any custom ones
            custom_models = [m for m in config.models if m not in AVAILABLE_MODELS]
            config.models = list(AVAILABLE_MODELS) + custom_models
            config.save(settings_path=settings_path, auth_path=auth_path)
        except Exception:
            config = cls()

        if auth_path.exists():
            try:
                auth_data = yaml.safe_load(auth_path.read_text()) or {}
                if isinstance(auth_data, dict):
                    config.credentials = {k: str(v) for k, v in auth_data.items()}
            except Exception:
                pass

        for key, value in config.credentials.items():
            os.environ.setdefault(key, str(value))

        return config

    def save(
        self,
        settings_path: Path = SETTINGS_PATH,
        auth_path: Path = AUTH_PATH,
    ) -> None:
        """Persist settings and credentials to their respective files."""
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        _write_yaml(
            settings_path,
            {
                "settings": self.settings.model_dump(by_alias=True),
                "models": self.models,
            },
        )

        if self.credentials:
            _secure_dir(auth_path.parent)
            _write_yaml(auth_path, dict(self.credentials))
            _secure_file(auth_path)

    def set_api_key(self, key_name: str, key_value: str) -> None:
        """Store an API key in credentials, inject it into the environment, and persist."""
        self.credentials[key_name] = key_value
        os.environ[key_name] = key_value
        self.save()
