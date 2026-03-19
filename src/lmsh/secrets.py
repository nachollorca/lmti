"""Secret management for lmsh.

Loads and persists API keys from ``~/.config/lmsh/.env`` so that credentials
survive across sessions without requiring manual shell-level configuration.
"""

import os
from pathlib import Path

ENV_PATH = Path.home() / ".config" / "lmsh" / ".env"


def load_env() -> None:
    """Load environment variables from ``~/.config/lmsh/.env``.

    Creates the file and parent directories when they do not exist.
    Existing environment variables are **not** overwritten (``os.environ``
    takes precedence over the file).
    """
    if not ENV_PATH.exists():
        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        ENV_PATH.touch()
        return

    for key, value in _parse_env(ENV_PATH).items():
        os.environ.setdefault(key, value)


def save_api_key(key_name: str, key_value: str) -> None:
    """Persist an API key to ``~/.config/lmsh/.env`` and set it in the process.

    If the key already exists in the file it is updated in place; otherwise it
    is appended.  The value is also injected into ``os.environ`` so it is
    available immediately.
    """
    os.environ[key_name] = key_value

    env_vars = _parse_env(ENV_PATH) if ENV_PATH.exists() else {}
    env_vars[key_name] = key_value

    lines = [f"{k}={v}" for k, v in env_vars.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n")


def _parse_env(path: Path) -> dict[str, str]:
    """Parse a ``.env`` file into a dictionary of key-value pairs.

    Blank lines and lines starting with ``#`` are ignored.  Surrounding
    quotes (single or double) on values are stripped.
    """
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        env[key] = value
    return env
