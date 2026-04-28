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
