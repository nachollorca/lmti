"""Shared test helpers."""

import io

import pytest
from rich.console import Console


@pytest.fixture
def console():
    """A Rich Console writing to an in-memory buffer."""
    buf = io.StringIO()
    return Console(file=buf, force_terminal=False, width=120, record=True)


@pytest.fixture
def fake_prompt(monkeypatch):
    """Queue canned answers for prompt_toolkit.PromptSession.prompt.

    Usage:
        fake_prompt(["first", "second"])
    """

    def _install(answers):
        queue = list(answers)

        def _fake(self, *args, **kwargs):
            if not queue:
                raise AssertionError("PromptSession.prompt called more times than expected")
            return queue.pop(0)

        from prompt_toolkit import PromptSession

        monkeypatch.setattr(PromptSession, "prompt", _fake)
        return queue

    return _install


@pytest.fixture
def config_paths(monkeypatch, tmp_path):
    """Redirect settings and auth files to a temporary directory."""
    settings = tmp_path / "lmti.yaml"
    auth = tmp_path / "auth.yaml"
    monkeypatch.setattr("lmti.config.SETTINGS_PATH", settings)
    monkeypatch.setattr("lmti.config.AUTH_PATH", auth)
    return settings, auth
