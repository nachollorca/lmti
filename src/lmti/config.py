"""Configuration management for lmti.

Loads and persists configuration from ``~/.config/lmti/config.yaml``.
"""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

CONFIG_PATH = Path.home() / ".config" / "lmti" / "config.yaml"

AVAILABLE_MODELS = [
    "mistral:mistral-small-2603",
    "mistral:mistral-large-2512",
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

    model_config = {"populate_by_name": True}


class Config(BaseModel):
    """Main configuration including credentials and settings."""

    credentials: dict[str, str] = Field(default_factory=dict)
    settings: Settings = Field(default_factory=Settings)
    models: list[str] = Field(default_factory=lambda: list(AVAILABLE_MODELS))

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        """Load configuration from disk, creating defaults if missing.

        Credentials are injected into ``os.environ``.
        """
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            config = cls()
            config.save(path)
            return config

        try:
            data = yaml.safe_load(path.read_text()) or {}
            config = cls(**data)

            # Sync available models if they differ from the constant
            if config.models != AVAILABLE_MODELS:
                config.models = list(AVAILABLE_MODELS)
                config.save(path)
        except Exception:
            config = cls()

        for key, value in config.credentials.items():
            os.environ.setdefault(key, str(value))

        return config

    def save(self, path: Path = CONFIG_PATH) -> None:
        """Persist current configuration to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            yaml.dump(self.model_dump(), f, sort_keys=False)

    def set_api_key(self, key_name: str, key_value: str) -> None:
        """Store an API key in credentials, inject it into the environment, and persist."""
        self.credentials[key_name] = key_value
        os.environ[key_name] = key_value
        self.save()
